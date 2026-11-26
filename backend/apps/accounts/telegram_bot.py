"""The FreeCook Telegram bot: confirms logins started on the site.

``handle_update`` is the whole bot. In production Telegram posts updates
to the webhook view; in development ``run_polling`` fetches them, because
localhost cannot receive webhooks. Both call ``handle_update``.

Telegram's API addresses contain the bot token, so errors are logged
without them.
"""

import json
import logging
import time
import urllib.request

from django.conf import settings
from django.db import close_old_connections

from apps.accounts.services.telegram_login import (
    TelegramLoginAlreadyConfirmedError,
    TelegramLoginError,
    confirm_login_request,
    find_open_login_request,
)

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/{method}"
REQUEST_TIMEOUT_SECONDS = 10
POLL_TIMEOUT_SECONDS = 30
POLL_RETRY_DELAY_SECONDS = 5

START_COMMAND = "/start"
CONFIRM_CALLBACK_PREFIX = "confirm:"

CONFIRM_PROMPT_TEXT = (
    "Підтвердьте вхід у FreeCook. "
    "Якщо це були не ви, просто проігноруйте це повідомлення."
)
CONFIRM_BUTTON_TEXT = "Підтвердити вхід"
LOGIN_CONFIRMED_TEXT = "Вхід підтверджено. Поверніться на сайт, він відкриється сам."
EXPIRED_TEXT = "Посилання застаріло. Поверніться на сайт і спробуйте ще раз."
ALREADY_CONFIRMED_TEXT = "Цей вхід уже підтверджено."
HELP_TEXT = "Щоб увійти у FreeCook, натисніть «Увійти через Telegram» на сайті."


class TelegramError(Exception):
    """A call to the Telegram Bot API failed."""


def call_telegram_api(method, payload=None, timeout_seconds=REQUEST_TIMEOUT_SECONDS):
    """Call a Bot API method and return its ``result``."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        raise TelegramError("TELEGRAM_BOT_TOKEN is not set.")
    request = urllib.request.Request(
        TELEGRAM_API_URL.format(token=token, method=method),
        data=json.dumps(payload or {}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = json.load(response)
    except (OSError, ValueError) as error:
        # Only the error class: its text could repeat the address and token.
        raise TelegramError(f"{method} failed: {type(error).__name__}.") from None
    if not isinstance(body, dict) or not body.get("ok"):
        raise TelegramError(f"{method} was refused by Telegram.")
    return body.get("result")


def handle_update(update):
    """React to one update from Telegram. Never raises on odd input."""
    if not isinstance(update, dict):
        return
    message = update.get("message")
    if isinstance(message, dict):
        _handle_message(message)
    callback_query = update.get("callback_query")
    if isinstance(callback_query, dict):
        _handle_callback_query(callback_query)


def poll_updates_once(offset=None):
    """Fetch and handle one batch of updates; return the next offset."""
    payload = {
        "timeout": POLL_TIMEOUT_SECONDS,
        "allowed_updates": ["message", "callback_query"],
    }
    if offset is not None:
        payload["offset"] = offset
    updates = call_telegram_api(
        "getUpdates",
        payload,
        timeout_seconds=POLL_TIMEOUT_SECONDS + REQUEST_TIMEOUT_SECONDS,
    )
    for update in updates:
        offset = update["update_id"] + 1
        # The bot runs for days: drop database connections the server closed.
        close_old_connections()
        try:
            handle_update(update)
        except Exception:
            logger.exception("The bot failed to handle an update.")
    return offset


def run_polling():
    """Handle updates forever. For local development only."""
    # Telegram refuses polling while a webhook is set.
    call_telegram_api("deleteWebhook")
    offset = None
    while True:
        try:
            offset = poll_updates_once(offset)
        except TelegramError as error:
            logger.warning("Polling failed: %s", error)
            time.sleep(POLL_RETRY_DELAY_SECONDS)


def _handle_message(message):
    chat = message.get("chat")
    text = message.get("text")
    if not isinstance(chat, dict) or not isinstance(text, str):
        return
    if chat.get("type") != "private" or not isinstance(chat.get("id"), int):
        return
    parts = text.split()
    # In groups Telegram writes "/start@BotName"; the name is not needed.
    if not parts or parts[0].split("@")[0] != START_COMMAND:
        return
    chat_id = chat["id"]
    if len(parts) < 2:
        _send_message(chat_id, HELP_TEXT)
        return
    token = parts[1]
    try:
        find_open_login_request(token)
    except TelegramLoginAlreadyConfirmedError:
        _send_message(chat_id, ALREADY_CONFIRMED_TEXT)
    except TelegramLoginError:
        _send_message(chat_id, EXPIRED_TEXT)
    else:
        _send_message(
            chat_id,
            CONFIRM_PROMPT_TEXT,
            reply_markup={
                "inline_keyboard": [
                    [
                        {
                            "text": CONFIRM_BUTTON_TEXT,
                            "callback_data": CONFIRM_CALLBACK_PREFIX + token,
                        }
                    ]
                ]
            },
        )


def _handle_callback_query(callback_query):
    data = callback_query.get("data")
    sender = callback_query.get("from")
    query_id = callback_query.get("id")
    if not isinstance(data, str) or not data.startswith(CONFIRM_CALLBACK_PREFIX):
        return
    if not isinstance(sender, dict) or not isinstance(sender.get("id"), int):
        return
    token = data.removeprefix(CONFIRM_CALLBACK_PREFIX)
    try:
        confirm_login_request(token, sender["id"])
    except TelegramLoginAlreadyConfirmedError:
        reply_text = ALREADY_CONFIRMED_TEXT
    except TelegramLoginError:
        reply_text = EXPIRED_TEXT
    else:
        reply_text = LOGIN_CONFIRMED_TEXT
    _call_quietly("answerCallbackQuery", {"callback_query_id": query_id})
    message = callback_query.get("message")
    if isinstance(message, dict) and isinstance(message.get("message_id"), int):
        chat = message.get("chat")
        if isinstance(chat, dict) and isinstance(chat.get("id"), int):
            # Replacing the text also removes the button, so it cannot be
            # pressed twice.
            _call_quietly(
                "editMessageText",
                {
                    "chat_id": chat["id"],
                    "message_id": message["message_id"],
                    "text": reply_text,
                },
            )


def _send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    _call_quietly("sendMessage", payload)


def _call_quietly(method, payload):
    # A reply that cannot be delivered must not undo a confirmed login.
    try:
        call_telegram_api(method, payload)
    except TelegramError as error:
        logger.warning("The bot could not reply: %s", error)
