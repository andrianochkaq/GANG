import io
import json
import urllib.error
from datetime import UTC, datetime, timedelta

import pytest
from django.core.management import call_command

from apps.accounts import telegram_bot
from apps.accounts.management.commands import run_telegram_bot
from apps.accounts.models import TelegramLoginRequest
from apps.accounts.services import telegram_login
from apps.accounts.services.telegram_login import start_login_request
from apps.accounts.telegram_bot import (
    CONFIRM_BUTTON_TEXT,
    CONFIRM_CALLBACK_PREFIX,
    EXPIRED_TEXT,
    HELP_TEXT,
    LOGIN_CONFIRMED_TEXT,
    TelegramError,
    call_telegram_api,
    handle_update,
    poll_updates_once,
)

pytestmark = pytest.mark.django_db

CHAT_ID = 555
TELEGRAM_ID = 123456789
OTHER_TELEGRAM_ID = 987654321
BOT_TOKEN = "123456:test-bot-token"


class FakeClock:
    def __init__(self):
        self.now = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)

    def advance(self, **time_parts):
        self.now += timedelta(**time_parts)


@pytest.fixture(autouse=True)
def keep_test_connection(monkeypatch):
    # Closing "old" connections would close the connection of the test's
    # own transaction.
    monkeypatch.setattr(telegram_bot, "close_old_connections", lambda: None)


@pytest.fixture
def clock(monkeypatch):
    fake_clock = FakeClock()
    monkeypatch.setattr(telegram_login, "_get_current_time", lambda: fake_clock.now)
    return fake_clock


@pytest.fixture
def api_calls(monkeypatch):
    calls = []

    def record_call(method, payload=None, timeout_seconds=None):
        calls.append((method, payload))
        return True

    monkeypatch.setattr(telegram_bot, "call_telegram_api", record_call)
    return calls


def build_start_update(text, chat_type="private"):
    return {
        "update_id": 1,
        "message": {
            "message_id": 10,
            "chat": {"id": CHAT_ID, "type": chat_type},
            "from": {"id": TELEGRAM_ID},
            "text": text,
        },
    }


def build_confirm_update(token, sender_id=TELEGRAM_ID):
    return {
        "update_id": 2,
        "callback_query": {
            "id": "query-1",
            "from": {"id": sender_id},
            "data": CONFIRM_CALLBACK_PREFIX + token,
            "message": {"message_id": 11, "chat": {"id": CHAT_ID}},
        },
    }


def read_method_names(api_calls):
    return [method for method, _ in api_calls]


# --- /start ---


def test_start_with_a_token_offers_the_confirm_button(clock, api_calls):
    login_request = start_login_request()

    handle_update(build_start_update(f"/start {login_request.token}"))

    assert read_method_names(api_calls) == ["sendMessage"]
    payload = api_calls[0][1]
    assert payload["chat_id"] == CHAT_ID
    button = payload["reply_markup"]["inline_keyboard"][0][0]
    assert button["text"] == CONFIRM_BUTTON_TEXT
    assert button["callback_data"] == CONFIRM_CALLBACK_PREFIX + login_request.token
    login_request.refresh_from_db()
    assert login_request.telegram_id is None


def test_callback_data_fits_the_telegram_limit(clock):
    login_request = start_login_request()

    callback_data = CONFIRM_CALLBACK_PREFIX + login_request.token

    assert len(callback_data.encode()) <= 64


def test_start_command_may_carry_the_bot_name(clock, api_calls):
    login_request = start_login_request()

    handle_update(build_start_update(f"/start@FreeCookBot {login_request.token}"))

    assert "reply_markup" in api_calls[0][1]


def test_start_without_a_token_explains_how_to_log_in(clock, api_calls):
    handle_update(build_start_update("/start"))

    assert api_calls == [("sendMessage", {"chat_id": CHAT_ID, "text": HELP_TEXT})]


def test_start_with_an_unknown_token_says_the_link_is_stale(clock, api_calls):
    handle_update(build_start_update("/start no-such-token"))

    assert api_calls == [("sendMessage", {"chat_id": CHAT_ID, "text": EXPIRED_TEXT})]


def test_start_with_an_expired_token_says_the_link_is_stale(clock, api_calls):
    login_request = start_login_request()
    clock.advance(minutes=5)

    handle_update(build_start_update(f"/start {login_request.token}"))

    assert api_calls == [("sendMessage", {"chat_id": CHAT_ID, "text": EXPIRED_TEXT})]


def test_messages_from_group_chats_are_ignored(clock, api_calls):
    login_request = start_login_request()

    handle_update(build_start_update(f"/start {login_request.token}", "group"))

    assert api_calls == []


def test_other_messages_are_ignored(clock, api_calls):
    handle_update(build_start_update("hello"))

    assert api_calls == []


# --- the Confirm button ---


def test_confirm_button_ties_the_request_to_the_sender(clock, api_calls):
    login_request = start_login_request()

    handle_update(build_confirm_update(login_request.token))

    login_request.refresh_from_db()
    assert login_request.telegram_id == TELEGRAM_ID
    assert read_method_names(api_calls) == ["answerCallbackQuery", "editMessageText"]
    assert api_calls[0][1] == {"callback_query_id": "query-1"}
    assert api_calls[1][1] == {
        "chat_id": CHAT_ID,
        "message_id": 11,
        "text": LOGIN_CONFIRMED_TEXT,
    }


def test_confirm_button_is_refused_after_five_minutes(clock, api_calls):
    login_request = start_login_request()
    clock.advance(minutes=5)

    handle_update(build_confirm_update(login_request.token))

    login_request.refresh_from_db()
    assert login_request.telegram_id is None
    assert api_calls[1][1]["text"] == EXPIRED_TEXT


def test_second_person_cannot_take_over_a_confirmed_request(clock, api_calls):
    login_request = start_login_request()
    handle_update(build_confirm_update(login_request.token))

    handle_update(build_confirm_update(login_request.token, OTHER_TELEGRAM_ID))

    login_request.refresh_from_db()
    assert login_request.telegram_id == TELEGRAM_ID


def test_unknown_buttons_are_ignored(clock, api_calls):
    update = build_confirm_update("x")
    update["callback_query"]["data"] = "something-else"

    handle_update(update)

    assert api_calls == []


def test_failed_reply_does_not_undo_the_confirmation(clock, monkeypatch):
    def fail_call(method, payload=None, timeout_seconds=None):
        raise TelegramError("Telegram is down.")

    monkeypatch.setattr(telegram_bot, "call_telegram_api", fail_call)
    login_request = start_login_request()

    handle_update(build_confirm_update(login_request.token))

    login_request.refresh_from_db()
    assert login_request.telegram_id == TELEGRAM_ID


@pytest.mark.parametrize(
    "update",
    [
        None,
        [],
        "text",
        {},
        {"message": "text"},
        {"message": {"chat": "x", "text": "/start x"}},
        {"message": {"chat": {"id": "1", "type": "private"}, "text": "/start x"}},
        {"callback_query": {"data": 5}},
        {"callback_query": {"data": "confirm:x", "from": "x"}},
        {"callback_query": {"data": "confirm:x", "from": {"id": "1"}}},
    ],
)
def test_odd_updates_are_ignored(clock, api_calls, update):
    handle_update(update)

    assert api_calls == []
    assert TelegramLoginRequest.objects.count() == 0


# --- Bot API calls ---


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


@pytest.fixture
def bot_token(settings):
    settings.TELEGRAM_BOT_TOKEN = BOT_TOKEN


def test_api_call_posts_json_and_returns_the_result(monkeypatch, bot_token):
    sent = {}

    def fake_urlopen(request, timeout):
        sent["url"] = request.full_url
        sent["body"] = json.loads(request.data)
        sent["timeout"] = timeout
        return FakeResponse(json.dumps({"ok": True, "result": [1, 2]}).encode())

    monkeypatch.setattr(telegram_bot.urllib.request, "urlopen", fake_urlopen)

    result = call_telegram_api("getUpdates", {"offset": 5})

    assert result == [1, 2]
    assert sent["url"] == f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    assert sent["body"] == {"offset": 5}
    assert sent["timeout"] == telegram_bot.REQUEST_TIMEOUT_SECONDS


def test_api_call_refused_by_telegram_raises(monkeypatch, bot_token):
    body = json.dumps({"ok": False, "description": "Bad Request"}).encode()
    monkeypatch.setattr(
        telegram_bot.urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse(body),
    )

    with pytest.raises(TelegramError):
        call_telegram_api("sendMessage", {})


@pytest.mark.parametrize(
    "error",
    [
        urllib.error.URLError(f"cannot reach /bot{BOT_TOKEN}/sendMessage"),
        TimeoutError(f"timed out at /bot{BOT_TOKEN}/sendMessage"),
        ConnectionResetError(f"reset at /bot{BOT_TOKEN}/sendMessage"),
    ],
)
def test_network_errors_become_telegram_errors_without_the_token(
    monkeypatch, bot_token, error
):
    def failing_urlopen(request, timeout):
        raise error

    monkeypatch.setattr(telegram_bot.urllib.request, "urlopen", failing_urlopen)

    with pytest.raises(TelegramError) as error_info:
        call_telegram_api("sendMessage", {})

    assert BOT_TOKEN not in str(error_info.value)


def test_non_json_answer_becomes_a_telegram_error(monkeypatch, bot_token):
    monkeypatch.setattr(
        telegram_bot.urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse(b"<html>"),
    )

    with pytest.raises(TelegramError):
        call_telegram_api("sendMessage", {})


def test_api_call_without_a_token_raises(settings):
    settings.TELEGRAM_BOT_TOKEN = ""

    with pytest.raises(TelegramError):
        call_telegram_api("sendMessage", {})


# --- polling ---


def test_polling_handles_updates_and_moves_the_offset(clock, monkeypatch):
    login_request = start_login_request()
    calls = []
    updates = [
        {**build_start_update(f"/start {login_request.token}"), "update_id": 40},
        {**build_confirm_update(login_request.token), "update_id": 41},
    ]

    def fake_call(method, payload=None, timeout_seconds=None):
        calls.append((method, payload))
        return updates if method == "getUpdates" else True

    monkeypatch.setattr(telegram_bot, "call_telegram_api", fake_call)

    next_offset = poll_updates_once(offset=30)

    assert next_offset == 42
    assert calls[0][0] == "getUpdates"
    assert calls[0][1]["offset"] == 30
    login_request.refresh_from_db()
    assert login_request.telegram_id == TELEGRAM_ID


def test_polling_keeps_the_offset_when_there_are_no_updates(monkeypatch):
    monkeypatch.setattr(telegram_bot, "call_telegram_api", lambda *args, **kwargs: [])

    assert poll_updates_once(offset=7) == 7
    assert poll_updates_once() is None


def test_polling_survives_a_broken_update(monkeypatch):
    def break_handler(update):
        raise RuntimeError("boom")

    monkeypatch.setattr(telegram_bot, "handle_update", break_handler)
    monkeypatch.setattr(
        telegram_bot,
        "call_telegram_api",
        lambda *args, **kwargs: [{"update_id": 3}],
    )

    assert poll_updates_once() == 4


# --- the management command ---


def test_command_without_a_token_explains_and_does_not_poll(settings, monkeypatch):
    settings.TELEGRAM_BOT_TOKEN = ""
    started = []
    monkeypatch.setattr(run_telegram_bot, "run_polling", lambda: started.append(True))
    output = io.StringIO()

    call_command("run_telegram_bot", stdout=output)

    assert "TELEGRAM_BOT_TOKEN" in output.getvalue()
    assert started == []


def test_command_with_a_token_starts_polling(settings, monkeypatch):
    settings.TELEGRAM_BOT_TOKEN = BOT_TOKEN
    started = []
    monkeypatch.setattr(run_telegram_bot, "run_polling", lambda: started.append(True))

    call_command("run_telegram_bot", stdout=io.StringIO())

    assert started == [True]
