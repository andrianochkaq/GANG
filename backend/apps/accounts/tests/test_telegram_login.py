from datetime import UTC, datetime, timedelta

import pytest

from apps.accounts.models import TelegramLoginRequest, User
from apps.accounts.services import telegram_login
from apps.accounts.services.telegram_login import (
    LOGIN_TTL_MINUTES,
    TelegramLoginAlreadyConfirmedError,
    TelegramLoginExpiredError,
    TelegramLoginNotFoundError,
    confirm_login_request,
    delete_expired_login_requests,
    find_open_login_request,
    read_login_result,
    start_login_request,
)

pytestmark = pytest.mark.django_db

TELEGRAM_ID = 123456789
OTHER_TELEGRAM_ID = 987654321


class FakeClock:
    def __init__(self):
        self.now = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)

    def advance(self, **time_parts):
        self.now += timedelta(**time_parts)


@pytest.fixture
def clock(monkeypatch):
    fake_clock = FakeClock()
    monkeypatch.setattr(telegram_login, "_get_current_time", lambda: fake_clock.now)
    return fake_clock


def test_start_creates_a_request_valid_for_five_minutes(clock):
    login_request = start_login_request()

    assert LOGIN_TTL_MINUTES == 5
    assert login_request.created_at == clock.now
    assert login_request.expires_at == clock.now + timedelta(minutes=5)
    assert login_request.telegram_id is None
    assert login_request.is_used is False


def test_token_fits_a_telegram_deep_link(clock):
    login_request = start_login_request()

    token = login_request.token
    assert 1 <= len(token) <= 64
    assert token.replace("-", "").replace("_", "").isalnum()
    assert token.isascii()


def test_every_request_has_its_own_token(clock):
    first_request = start_login_request()
    second_request = start_login_request()

    assert first_request.token != second_request.token


def test_confirm_ties_the_request_to_the_telegram_id(clock):
    login_request = start_login_request()
    clock.advance(seconds=30)

    confirm_login_request(login_request.token, TELEGRAM_ID)

    login_request.refresh_from_db()
    assert login_request.telegram_id == TELEGRAM_ID
    assert login_request.confirmed_at == clock.now


def test_confirm_works_until_the_last_second(clock):
    login_request = start_login_request()
    clock.advance(minutes=4, seconds=59)

    confirm_login_request(login_request.token, TELEGRAM_ID)

    login_request.refresh_from_db()
    assert login_request.telegram_id == TELEGRAM_ID


def test_request_older_than_five_minutes_cannot_be_confirmed(clock):
    login_request = start_login_request()
    clock.advance(minutes=5)

    with pytest.raises(TelegramLoginExpiredError):
        confirm_login_request(login_request.token, TELEGRAM_ID)

    login_request.refresh_from_db()
    assert login_request.telegram_id is None


def test_unknown_token_cannot_be_confirmed(clock):
    with pytest.raises(TelegramLoginNotFoundError):
        confirm_login_request("no-such-token", TELEGRAM_ID)


def test_first_confirmation_wins(clock):
    login_request = start_login_request()
    confirm_login_request(login_request.token, TELEGRAM_ID)

    with pytest.raises(TelegramLoginAlreadyConfirmedError):
        confirm_login_request(login_request.token, OTHER_TELEGRAM_ID)

    login_request.refresh_from_db()
    assert login_request.telegram_id == TELEGRAM_ID


def test_find_open_returns_a_fresh_request(clock):
    login_request = start_login_request()

    assert find_open_login_request(login_request.token) == login_request


def test_find_open_refuses_a_confirmed_request(clock):
    login_request = start_login_request()
    confirm_login_request(login_request.token, TELEGRAM_ID)

    with pytest.raises(TelegramLoginAlreadyConfirmedError):
        find_open_login_request(login_request.token)


def test_find_open_refuses_an_expired_request(clock):
    login_request = start_login_request()
    clock.advance(minutes=5)

    with pytest.raises(TelegramLoginExpiredError):
        find_open_login_request(login_request.token)


def test_find_open_refuses_an_unknown_token(clock):
    with pytest.raises(TelegramLoginNotFoundError):
        find_open_login_request("no-such-token")


def test_result_is_pending_until_the_request_is_confirmed(clock):
    login_request = start_login_request()

    assert read_login_result(login_request.token) is None
    assert User.objects.count() == 0


def test_confirmed_request_creates_an_account_once(clock):
    login_request = start_login_request()
    confirm_login_request(login_request.token, TELEGRAM_ID)

    user, is_new_user = read_login_result(login_request.token)

    assert is_new_user is True
    assert user.telegram_id == TELEGRAM_ID
    login_request.refresh_from_db()
    assert login_request.is_used is True
    with pytest.raises(TelegramLoginNotFoundError):
        read_login_result(login_request.token)
    assert User.objects.count() == 1


def test_new_account_has_no_password_and_no_other_contact(clock):
    login_request = start_login_request()
    confirm_login_request(login_request.token, TELEGRAM_ID)

    user, _ = read_login_result(login_request.token)

    user.refresh_from_db()
    assert user.password is None
    assert user.has_usable_password() is False
    assert user.email is None
    assert user.phone is None


def test_same_telegram_id_always_logs_into_the_same_account(clock):
    first_request = start_login_request()
    confirm_login_request(first_request.token, TELEGRAM_ID)
    first_user, _ = read_login_result(first_request.token)
    second_request = start_login_request()
    confirm_login_request(second_request.token, TELEGRAM_ID)

    second_user, is_new_user = read_login_result(second_request.token)

    assert is_new_user is False
    assert second_user.pk == first_user.pk
    assert User.objects.count() == 1


def test_different_telegram_ids_get_different_accounts(clock):
    first_request = start_login_request()
    confirm_login_request(first_request.token, TELEGRAM_ID)
    second_request = start_login_request()
    confirm_login_request(second_request.token, OTHER_TELEGRAM_ID)

    first_user, _ = read_login_result(first_request.token)
    second_user, _ = read_login_result(second_request.token)

    assert first_user.pk != second_user.pk
    assert first_user.nickname != second_user.nickname


def test_confirmed_request_is_not_collectable_after_it_expires(clock):
    login_request = start_login_request()
    confirm_login_request(login_request.token, TELEGRAM_ID)
    clock.advance(minutes=5)

    with pytest.raises(TelegramLoginExpiredError):
        read_login_result(login_request.token)

    assert User.objects.count() == 0


def test_delete_expired_requests_keeps_open_ones(clock):
    expired_request = start_login_request()
    clock.advance(minutes=6)
    open_request = start_login_request()

    deleted_count = delete_expired_login_requests()

    assert deleted_count == 1
    assert list(TelegramLoginRequest.objects.all()) == [open_request]
    assert not TelegramLoginRequest.objects.filter(pk=expired_request.pk).exists()


def test_request_is_shown_without_its_token(clock):
    login_request = start_login_request()

    assert login_request.token not in str(login_request)
