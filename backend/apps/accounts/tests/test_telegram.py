from datetime import UTC, datetime, timedelta

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts import telegram_bot
from apps.accounts.models import TelegramLoginRequest, User
from apps.accounts.services import telegram_login
from apps.accounts.telegram_bot import CONFIRM_CALLBACK_PREFIX

pytestmark = pytest.mark.django_db

START_URL = "/api/auth/telegram/start/"
WEBHOOK_URL = "/api/auth/telegram/webhook/"
WEBHOOK_SECRET = "test-webhook-secret"
SECRET_HEADER = "HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN"
BOT_USERNAME = "FreeCookTestBot"
CHAT_ID = 555
TELEGRAM_ID = 123456789


class FakeClock:
    def __init__(self):
        self.now = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)

    def advance(self, **time_parts):
        self.now += timedelta(**time_parts)


@pytest.fixture(autouse=True)
def isolated_environment(settings, monkeypatch):
    # Throttle counters must not leak between tests or into a real Redis.
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "telegram-login-tests",
        },
    }
    settings.TELEGRAM_BOT_USERNAME = BOT_USERNAME
    settings.TELEGRAM_WEBHOOK_SECRET = WEBHOOK_SECRET
    cache.clear()
    # The bot must never reach the real Telegram from a test.
    monkeypatch.setattr(telegram_bot, "close_old_connections", lambda: None)


@pytest.fixture
def api_calls(monkeypatch):
    calls = []

    def record_call(method, payload=None, timeout_seconds=None):
        calls.append((method, payload))
        return True

    monkeypatch.setattr(telegram_bot, "call_telegram_api", record_call)
    return calls


@pytest.fixture
def clock(monkeypatch):
    fake_clock = FakeClock()
    monkeypatch.setattr(telegram_login, "_get_current_time", lambda: fake_clock.now)
    return fake_clock


@pytest.fixture
def api_client():
    return APIClient()


def start_login(api_client):
    return api_client.post(START_URL, format="json")


def read_status(api_client, token):
    return api_client.get(f"/api/auth/telegram/status/{token}/")


def post_update(api_client, update, secret=WEBHOOK_SECRET):
    extra = {SECRET_HEADER: secret} if secret is not None else {}
    return api_client.post(WEBHOOK_URL, update, format="json", **extra)


def build_start_update(token):
    return {
        "update_id": 1,
        "message": {
            "message_id": 10,
            "chat": {"id": CHAT_ID, "type": "private"},
            "from": {"id": TELEGRAM_ID},
            "text": f"/start {token}",
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


# --- start ---


def test_start_returns_a_deep_link_to_the_bot(api_client):
    response = start_login(api_client)

    assert response.status_code == 200
    body = response.json()
    assert body["deep_link"] == f"https://t.me/{BOT_USERNAME}?start={body['token']}"
    assert body["expires_in_seconds"] == 300
    assert body["poll_interval_seconds"] == 2
    assert TelegramLoginRequest.objects.get().token == body["token"]


def test_start_needs_no_token_or_password(api_client):
    response = api_client.post(START_URL)

    assert response.status_code == 200


def test_start_without_a_bot_username_is_unavailable(api_client, settings):
    settings.TELEGRAM_BOT_USERNAME = ""

    response = start_login(api_client)

    assert response.status_code == 503
    assert response.json()["code"] == "telegram_unavailable"
    assert TelegramLoginRequest.objects.count() == 0


def test_start_is_throttled_per_ip_address(api_client):
    statuses = [start_login(api_client).status_code for _ in range(21)]

    assert statuses == [200] * 20 + [429]


# --- status ---


def test_status_is_pending_until_the_bot_confirms(api_client):
    token = start_login(api_client).json()["token"]

    response = read_status(api_client, token)

    assert response.status_code == 200
    assert response.json() == {"status": "pending"}
    assert User.objects.count() == 0


def test_status_of_an_unknown_token_is_not_found(api_client):
    response = read_status(api_client, "no-such-token")

    assert response.status_code == 404
    assert response.json()["code"] == "telegram_login_not_found"


def test_status_of_an_expired_request_is_gone(api_client, clock):
    token = start_login(api_client).json()["token"]
    clock.advance(minutes=5)

    response = read_status(api_client, token)

    assert response.status_code == 410
    assert response.json()["code"] == "telegram_login_expired"


# --- the whole flow ---


def test_login_through_the_bot_works_end_to_end(api_client, api_calls, clock):
    token = start_login(api_client).json()["token"]

    start_response = post_update(api_client, build_start_update(token))
    pending_response = read_status(api_client, token)
    confirm_response = post_update(api_client, build_confirm_update(token))
    login_response = read_status(api_client, token)

    assert start_response.status_code == 200
    assert api_calls[0][0] == "sendMessage"
    assert pending_response.json() == {"status": "pending"}
    assert confirm_response.status_code == 200
    assert login_response.status_code == 200
    body = login_response.json()
    assert body["status"] == "confirmed"
    assert body["is_new_user"] is True
    user = User.objects.get(telegram_id=TELEGRAM_ID)
    assert AccessToken(body["access"])["user_id"] == str(user.pk)
    assert body["refresh"]


def test_new_telegram_account_has_no_password(api_client, api_calls, clock):
    token = start_login(api_client).json()["token"]
    post_update(api_client, build_confirm_update(token))

    read_status(api_client, token)

    user = User.objects.get(telegram_id=TELEGRAM_ID)
    assert user.has_usable_password() is False


def test_login_can_be_collected_only_once(api_client, api_calls, clock):
    token = start_login(api_client).json()["token"]
    post_update(api_client, build_confirm_update(token))
    read_status(api_client, token)

    response = read_status(api_client, token)

    assert response.status_code == 404
    assert "access" not in response.json()


def test_same_telegram_id_logs_into_the_same_account(api_client, api_calls, clock):
    bodies = []
    for _ in range(2):
        token = start_login(api_client).json()["token"]
        post_update(api_client, build_confirm_update(token))
        bodies.append(read_status(api_client, token).json())

    first_user_id = AccessToken(bodies[0]["access"])["user_id"]
    second_user_id = AccessToken(bodies[1]["access"])["user_id"]
    assert bodies[0]["is_new_user"] is True
    assert bodies[1]["is_new_user"] is False
    assert first_user_id == second_user_id
    assert User.objects.count() == 1


def test_request_confirmed_after_five_minutes_logs_nobody_in(
    api_client, api_calls, clock
):
    token = start_login(api_client).json()["token"]
    clock.advance(minutes=5)

    confirm_response = post_update(api_client, build_confirm_update(token))
    status_response = read_status(api_client, token)

    assert confirm_response.status_code == 200
    assert TelegramLoginRequest.objects.get().telegram_id is None
    assert status_response.status_code == 410
    assert User.objects.count() == 0


def test_disabled_account_gets_no_tokens(api_client, api_calls, clock):
    User.objects.create_user("anna", telegram_id=TELEGRAM_ID, is_active=False)
    token = start_login(api_client).json()["token"]
    post_update(api_client, build_confirm_update(token))

    response = read_status(api_client, token)

    assert response.status_code == 403
    body = response.json()
    assert body["code"] == "account_disabled"
    assert "access" not in body
    assert "refresh" not in body


# --- the webhook secret ---


@pytest.mark.parametrize("secret", [None, "", "wrong-secret", "test-webhook-secre"])
def test_webhook_without_the_right_secret_is_rejected(
    api_client, api_calls, clock, secret
):
    token = start_login(api_client).json()["token"]

    response = post_update(api_client, build_confirm_update(token), secret)

    assert response.status_code == 403
    assert response.json()["code"] == "webhook_forbidden"
    assert TelegramLoginRequest.objects.get().telegram_id is None
    assert api_calls == []


def test_webhook_refuses_everything_while_no_secret_is_configured(
    api_client, api_calls, clock, settings
):
    token = start_login(api_client).json()["token"]
    settings.TELEGRAM_WEBHOOK_SECRET = ""

    without_header = post_update(api_client, build_confirm_update(token), None)
    with_empty_header = post_update(api_client, build_confirm_update(token), "")

    assert without_header.status_code == 403
    assert with_empty_header.status_code == 403
    assert TelegramLoginRequest.objects.get().telegram_id is None


def test_webhook_needs_no_user_token(api_client, api_calls, clock):
    token = start_login(api_client).json()["token"]

    response = post_update(api_client, build_confirm_update(token))

    assert response.status_code == 200


@pytest.mark.parametrize("update", [{}, [], {"message": "text"}])
def test_webhook_answers_200_to_updates_it_does_not_understand(
    api_client, api_calls, update
):
    response = post_update(api_client, update)

    assert response.status_code == 200
    assert api_calls == []
