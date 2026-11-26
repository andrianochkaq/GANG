from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import OneTimeCode, User
from apps.accounts.services import codes
from apps.accounts.services.codes import (
    CODE_TTL_MINUTES,
    MAX_CODE_ATTEMPTS,
    RESEND_COOLDOWN_SECONDS,
)

pytestmark = pytest.mark.django_db

EMAIL_ADDRESS = "anna@example.com"
PASSWORD = "pear-lamp-violet-92"
OTHER_PASSWORD = "cedar-maple-orbit-47"
REGISTER_URL = "/api/auth/email/register/"
VERIFY_URL = "/api/auth/email/verify/"
RESEND_URL = "/api/auth/email/resend-code/"
LOGIN_URL = "/api/auth/email/login/"


class FakeClock:
    def __init__(self):
        self.now = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)

    def advance(self, **time_parts):
        self.now += timedelta(**time_parts)


@pytest.fixture(autouse=True)
def local_memory_cache(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "email-view-tests",
        },
    }
    cache.clear()


@pytest.fixture(autouse=True)
def fast_password_hasher(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def clock(monkeypatch):
    fake_clock = FakeClock()
    monkeypatch.setattr(codes, "_get_current_time", lambda: fake_clock.now)
    return fake_clock


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def send_task():
    with patch("apps.accounts.views.email.send_email_code") as task:
        yield task


def post_json(api_client, url, data, **extra):
    return api_client.post(url, data, format="json", **extra)


def register(api_client, email=EMAIL_ADDRESS, password=PASSWORD, **extra):
    data = {"email": email, "password": password}
    return post_json(api_client, REGISTER_URL, data, **extra)


def verify(api_client, code, email=EMAIL_ADDRESS):
    return post_json(api_client, VERIFY_URL, {"email": email, "code": code})


def resend(api_client, email=EMAIL_ADDRESS):
    return post_json(api_client, RESEND_URL, {"email": email})


def log_in(api_client, email=EMAIL_ADDRESS, password=PASSWORD):
    data = {"email": email, "password": password}
    return post_json(api_client, LOGIN_URL, data)


def sent_code(send_task):
    return send_task.delay.call_args.args[1]


def wrong_code_for(code):
    return "000000" if code != "000000" else "111111"


def create_verified_user(**extra):
    return User.objects.create_user(
        "anna",
        email=EMAIL_ADDRESS,
        password=PASSWORD,
        is_email_verified=True,
        **extra,
    )


# Registration


def test_register_creates_an_unverified_user_and_sends_a_code(api_client, send_task):
    response = register(api_client)

    assert response.status_code == 201
    assert response.json() == {
        "email": EMAIL_ADDRESS,
        "resend_after_seconds": RESEND_COOLDOWN_SECONDS,
    }
    user = User.objects.get(email=EMAIL_ADDRESS)
    assert user.is_email_verified is False
    assert user.check_password(PASSWORD)
    send_task.delay.assert_called_once()
    email, code = send_task.delay.call_args.args
    assert email == EMAIL_ADDRESS
    assert len(code) == 6


def test_register_stores_the_email_in_lower_case(api_client, send_task):
    response = register(api_client, email=" Anna@Example.COM ")

    assert response.status_code == 201
    assert User.objects.get().email == EMAIL_ADDRESS


@pytest.mark.parametrize(
    "password",
    ["short1", "12345678", "password", EMAIL_ADDRESS],
)
def test_register_refuses_a_weak_password(api_client, send_task, password):
    response = register(api_client, password=password)

    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "validation_error"
    assert "password" in body["fields"]
    assert not User.objects.exists()
    send_task.delay.assert_not_called()


def test_register_refuses_a_missing_email_and_password(api_client, send_task):
    response = post_json(api_client, REGISTER_URL, {})

    assert response.status_code == 400
    assert set(response.json()["fields"]) == {"email", "password"}


def test_register_refuses_an_email_that_is_already_verified(api_client, send_task):
    create_verified_user()

    response = register(api_client, password=OTHER_PASSWORD)

    assert response.status_code == 409
    assert response.json()["code"] == "email_taken"
    send_task.delay.assert_not_called()


def test_register_again_resets_an_unverified_account(api_client, send_task, clock):
    register(api_client)
    clock.advance(seconds=RESEND_COOLDOWN_SECONDS + 1)

    response = register(api_client, password=OTHER_PASSWORD)

    assert response.status_code == 201
    assert User.objects.count() == 1
    assert User.objects.get().check_password(OTHER_PASSWORD)
    assert send_task.delay.call_count == 2


def test_register_again_too_soon_changes_nothing(api_client, send_task, clock):
    register(api_client)

    response = register(api_client, password=OTHER_PASSWORD)

    assert response.status_code == 429
    body = response.json()
    assert body["code"] == "code_resend_too_soon"
    assert 0 < body["retry_after_seconds"] <= RESEND_COOLDOWN_SECONDS
    assert response["Retry-After"] == str(body["retry_after_seconds"])
    assert User.objects.get().check_password(PASSWORD)
    assert send_task.delay.call_count == 1


def test_register_is_throttled_per_ip_address(api_client, send_task):
    for index in range(5):
        response = register(api_client, email=f"user{index}@example.com")
        assert response.status_code == 201

    response = register(api_client, email="user5@example.com")

    assert response.status_code == 429
    assert response.json()["code"] == "too_many_requests"
    assert response.has_header("Retry-After")


def test_register_is_throttled_per_email(api_client, send_task):
    for index in range(5):
        register(api_client, REMOTE_ADDR=f"203.0.113.{index}")

    response = register(api_client, REMOTE_ADDR="203.0.113.9")

    assert response.status_code == 429
    assert response.json()["code"] == "too_many_requests"


# Confirmation


def test_verify_marks_the_email_verified_and_returns_tokens(api_client, send_task):
    register(api_client)

    response = verify(api_client, sent_code(send_task))

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"access", "refresh"}
    user = User.objects.get(email=EMAIL_ADDRESS)
    assert user.is_email_verified is True
    assert user.last_login is not None
    assert AccessToken(body["access"])["user_id"] == str(user.id)


def test_verify_refuses_a_wrong_code(api_client, send_task):
    register(api_client)

    response = verify(api_client, wrong_code_for(sent_code(send_task)))

    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "code_invalid"
    assert body["attempts_left"] == MAX_CODE_ATTEMPTS - 1
    assert User.objects.get().is_email_verified is False


def test_verify_refuses_an_expired_code(api_client, send_task, clock):
    register(api_client)
    clock.advance(minutes=CODE_TTL_MINUTES + 1)

    response = verify(api_client, sent_code(send_task))

    assert response.status_code == 400
    assert response.json()["code"] == "code_expired"
    assert User.objects.get().is_email_verified is False


def test_verify_stops_after_too_many_wrong_codes(api_client, send_task):
    register(api_client)
    code = sent_code(send_task)
    for _ in range(MAX_CODE_ATTEMPTS):
        verify(api_client, wrong_code_for(code))

    response = verify(api_client, code)

    assert response.status_code == 400
    assert response.json()["code"] == "code_attempts_exceeded"
    assert User.objects.get().is_email_verified is False


def test_verify_refuses_an_email_that_never_registered(api_client):
    response = verify(api_client, "123456", email="ghost@example.com")

    assert response.status_code == 400
    assert response.json()["code"] == "code_invalid"


def test_verify_refuses_a_code_that_is_not_six_digits(api_client, send_task):
    register(api_client)

    response = verify(api_client, "12ab56")

    assert response.status_code == 400
    assert response.json()["code"] == "validation_error"
    assert "code" in response.json()["fields"]
    assert OneTimeCode.objects.get().attempt_count == 0


def test_a_code_works_only_once(api_client, send_task):
    register(api_client)
    code = sent_code(send_task)
    verify(api_client, code)

    response = verify(api_client, code)

    assert response.status_code == 400
    assert response.json()["code"] == "code_invalid"


# Login


def test_user_logs_in_only_after_entering_the_code(api_client, send_task):
    register(api_client)

    before_code = log_in(api_client)
    verify(api_client, sent_code(send_task))
    after_code = log_in(api_client)

    assert before_code.status_code == 403
    assert before_code.json()["code"] == "email_not_verified"
    assert "access" not in before_code.json()
    assert after_code.status_code == 200
    assert set(after_code.json()) == {"access", "refresh"}


def test_login_ignores_the_case_of_the_email(api_client):
    create_verified_user()

    response = log_in(api_client, email="ANNA@Example.com")

    assert response.status_code == 200


@pytest.mark.parametrize(
    ("email", "password"),
    [
        (EMAIL_ADDRESS, OTHER_PASSWORD),
        ("ghost@example.com", PASSWORD),
    ],
    ids=["wrong_password", "unknown_email"],
)
def test_login_refuses_wrong_credentials(api_client, email, password):
    create_verified_user()

    response = log_in(api_client, email=email, password=password)

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"


def test_login_does_not_reveal_an_unverified_account_to_a_wrong_password(
    api_client, send_task
):
    register(api_client)

    response = log_in(api_client, password=OTHER_PASSWORD)

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"


def test_login_refuses_a_disabled_account(api_client):
    create_verified_user(is_active=False)

    response = log_in(api_client)

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"


# Resending the code


def test_resend_sends_a_new_code_that_replaces_the_old_one(
    api_client, send_task, clock
):
    register(api_client)
    clock.advance(seconds=RESEND_COOLDOWN_SECONDS + 1)

    response = resend(api_client)

    assert response.status_code == 202
    assert send_task.delay.call_count == 2
    assert OneTimeCode.objects.filter(is_used=False).count() == 1
    assert verify(api_client, sent_code(send_task)).status_code == 200


def test_resend_too_soon_is_refused(api_client, send_task, clock):
    register(api_client)

    response = resend(api_client)

    assert response.status_code == 429
    assert response.json()["code"] == "code_resend_too_soon"
    assert send_task.delay.call_count == 1


def test_resend_answers_the_same_for_an_unknown_email(api_client, send_task):
    response = resend(api_client, email="ghost@example.com")

    assert response.status_code == 202
    assert response.json() == {
        "email": "ghost@example.com",
        "resend_after_seconds": RESEND_COOLDOWN_SECONDS,
    }
    send_task.delay.assert_not_called()


def test_resend_sends_nothing_to_a_verified_account(api_client, send_task):
    create_verified_user()

    response = resend(api_client)

    assert response.status_code == 202
    send_task.delay.assert_not_called()


# Schema


def test_schema_describes_the_email_endpoints(client):
    response = client.get("/api/schema/")

    assert response.status_code == 200
    for url in (REGISTER_URL, VERIFY_URL, RESEND_URL, LOGIN_URL):
        assert url.encode() in response.content
