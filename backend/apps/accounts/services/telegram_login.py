"""Login requests of the Telegram bot flow (docs/architecture.md, 7.1).

``start_login_request`` creates a request with a secret token. The token
travels to the bot inside a deep link. When the person presses "Confirm"
in the bot, ``confirm_login_request`` ties the request to their Telegram
id. The browser polls ``read_login_result`` and receives the account
once, and only while the request is younger than ``LOGIN_TTL_MINUTES``.
Every refusal is a ``TelegramLoginError`` subclass.
"""

import secrets
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.models import TelegramLoginRequest, User
from apps.accounts.services.phone_accounts import generate_nickname

LOGIN_TTL_MINUTES = 5
# 32 random bytes make a 43-character token, and Telegram accepts up to 64
# characters of A-Z, a-z, 0-9, _ and - in a deep link.
TOKEN_BYTES = 32


class TelegramLoginError(Exception):
    """Base class for every refusal of a Telegram login step."""


class TelegramLoginNotFoundError(TelegramLoginError):
    """No such request, or its sign-in was already handed out."""


class TelegramLoginExpiredError(TelegramLoginError):
    """The request is older than ``LOGIN_TTL_MINUTES``."""


class TelegramLoginAlreadyConfirmedError(TelegramLoginError):
    """Somebody has already pressed "Confirm" for this request."""


def start_login_request():
    """Create a request that is valid for ``LOGIN_TTL_MINUTES``."""
    now = _get_current_time()
    return TelegramLoginRequest.objects.create(
        token=secrets.token_urlsafe(TOKEN_BYTES),
        created_at=now,
        expires_at=now + timedelta(minutes=LOGIN_TTL_MINUTES),
    )


def find_open_login_request(token):
    """Return the request if the bot may still ask to confirm it."""
    login_request = _get_login_request(token)
    _check_not_expired(login_request)
    if login_request.telegram_id is not None:
        raise TelegramLoginAlreadyConfirmedError()
    return login_request


def confirm_login_request(token, telegram_id):
    """Tie the request to the Telegram id that pressed "Confirm"."""
    with transaction.atomic():
        login_request = _get_login_request(token, lock=True)
        _check_not_expired(login_request)
        if login_request.telegram_id is not None:
            raise TelegramLoginAlreadyConfirmedError()
        login_request.telegram_id = telegram_id
        login_request.confirmed_at = _get_current_time()
        login_request.save(update_fields=["telegram_id", "confirmed_at"])
    return login_request


def read_login_result(token):
    """Return ``(user, is_new_user)`` once, or ``None`` while unconfirmed.

    The account is created here when the Telegram id is new. After the
    result has been handed out the request is used up.
    """
    with transaction.atomic():
        login_request = _get_login_request(token, lock=True)
        _check_not_expired(login_request)
        if login_request.telegram_id is None:
            return None
        result = get_or_create_telegram_user(login_request.telegram_id)
        login_request.is_used = True
        login_request.save(update_fields=["is_used"])
    return result


def get_or_create_telegram_user(telegram_id):
    """Return ``(user, is_created)``; one Telegram id is one account.

    A new account has no password and a generated nickname that the
    person changes later.
    """
    user = User.objects.filter(telegram_id=telegram_id).first()
    if user is not None:
        return user, False
    try:
        with transaction.atomic():
            user = User.objects.create_user(
                generate_nickname(),
                telegram_id=telegram_id,
            )
    except IntegrityError:
        # Two first logins of one Telegram id can race: take the winner's row.
        user = User.objects.filter(telegram_id=telegram_id).first()
        if user is None:
            raise
        return user, False
    return user, True


def delete_expired_login_requests():
    """Delete requests that can no longer be confirmed; return how many."""
    deleted_count, _ = TelegramLoginRequest.objects.filter(
        expires_at__lte=_get_current_time(),
    ).delete()
    return deleted_count


def _get_current_time():
    return timezone.now()


def _get_login_request(token, lock=False):
    login_requests = TelegramLoginRequest.objects.filter(token=token, is_used=False)
    if lock:
        login_requests = login_requests.select_for_update()
    login_request = login_requests.first()
    if login_request is None:
        raise TelegramLoginNotFoundError()
    return login_request


def _check_not_expired(login_request):
    if login_request.expires_at <= _get_current_time():
        raise TelegramLoginExpiredError()
