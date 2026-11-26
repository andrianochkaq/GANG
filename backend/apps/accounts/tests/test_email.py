import re
from datetime import timedelta

import pytest
from django.core import mail
from django.core.cache import cache
from django.utils import timezone
from kombu.exceptions import OperationalError
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import CodePurpose, OneTimeCode, User
from apps.accounts.services.codes import MAX_CODE_ATTEMPTS
from apps.accounts.tasks import send_email_code

pytestmark = pytest.mark.django_db

REGISTER_URL = "/api/auth/email-register/"
CODE_URL = "/api/auth/email-code/"
VERIFY_URL = "/api/auth/email-verify/"
LOGIN_URL = "/api/auth/email-login/"
EMAIL = "anna@example.com"
PASSWORD = "correct-horse-battery"


@pytest.fixture(autouse=True)
def isolated_environment(settings, monkeypatch):
    # Throttle counters must not leak between tests or into a real Redis.
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "email-login-tests",
        },
    }
    cache.clear()
    # Run the task at once instead of sending it to a broker.
    monkeypatch.setattr(
        "apps.accounts.views.email.send_email_code.delay",
        send_email_code,
    )


@pytest.fixture
def api_client():
    return APIClient()


def register(api_client, email=EMAIL, password=PASSWORD):
    body = {"email": email, "password": password}
    return api_client.post(REGISTER_URL, body, format="json")


def verify(api_client, code, email=EMAIL):
    body = {"email": email, "code": code}
    return api_client.post(VERIFY_URL, body, format="json")


def log_in(api_client, email=EMAIL, password=PASSWORD):
    body = {"email": email, "password": password}
    return api_client.post(LOGIN_URL, body, format="json")


def read_sent_code():
    return re.search(r"[0-9]{6}", mail.outbox[-1].body).group()


def forget_cooldown():
    # Move the codes back in time so the resend cooldown does not get in the way.
    now = timezone.now()
    OneTimeCode.objects.update(
        created_at=now - timedelta(hours=2),
        expires_at=now - timedelta(hours=1),
    )


def wrong_code_for(code):
    return "000000" if code != "000000" else "111111"


# --- signing up ---


def test_register_sends_one_letter_with_a_code(api_client):
    response = register(api_client)

    assert response.status_code == 200
    assert response.json() == {"resend_after_seconds": 60}
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [EMAIL]
    assert len(read_sent_code()) == 6


def test_register_creates_an_unverified_user(api_client):
    register(api_client)

    user = User.objects.get(email=EMAIL)
    assert user.is_email_verified is False
    assert user.check_password(PASSWORD)
    assert OneTimeCode.objects.get().purpose == CodePurpose.EMAIL_VERIFICATION


def test_register_stores_the_email_in_lower_case(api_client):
    register(api_client, "  Anna@Example.COM ")

    assert User.objects.get().email == EMAIL
    assert mail.outbox[0].to == [EMAIL]


@pytest.mark.parametrize(
    "password",
    ["short1", "12345678901", "password1234", "anna@example.com"],
)
def test_register_refuses_a_weak_password(api_client, password):
    response = register(api_client, password=password)

    assert response.status_code == 400
    assert response.json()["code"] == "validation_error"
    assert "password" in response.json()["fields"]
    assert User.objects.count() == 0
    assert mail.outbox == []


@pytest.mark.parametrize(
    "body",
    [
        {"email": "not-an-email", "password": PASSWORD},
        {"email": "", "password": PASSWORD},
        {"email": EMAIL},
        {"password": PASSWORD},
    ],
)
def test_register_refuses_an_invalid_body(api_client, body):
    response = api_client.post(REGISTER_URL, body, format="json")

    assert response.status_code == 400
    assert response.json()["code"] == "validation_error"
    assert User.objects.count() == 0
    assert OneTimeCode.objects.count() == 0


def test_register_answers_the_same_for_a_confirmed_email(api_client):
    register(api_client)
    verify(api_client, read_sent_code())
    mail.outbox.clear()
    forget_cooldown()

    response = register(api_client, password="another-long-password")

    assert response.status_code == 200
    assert response.json() == {"resend_after_seconds": 60}
    assert mail.outbox == []
    assert User.objects.get().check_password(PASSWORD)


def test_register_again_before_confirming_sets_the_new_password(api_client):
    register(api_client)
    forget_cooldown()

    register(api_client, password="another-long-password")

    user = User.objects.get()
    assert user.check_password("another-long-password")
    assert len(mail.outbox) == 2


def test_register_is_refused_during_the_resend_cooldown(api_client):
    register(api_client)

    response = register(api_client)

    assert response.status_code == 429
    assert response.json()["code"] == "code_resend_too_soon"
    assert "Retry-After" in response.headers
    assert len(mail.outbox) == 1


def test_register_says_so_when_the_broker_is_down(api_client, monkeypatch):
    def fail_to_queue(*args, **kwargs):
        raise OperationalError("Connection refused")

    monkeypatch.setattr(
        "apps.accounts.views.email.send_email_code.delay",
        fail_to_queue,
    )

    response = register(api_client)

    assert response.status_code == 503
    assert response.json()["code"] == "email_unavailable"


# --- confirming the email ---


def test_verify_activates_the_account_and_returns_a_jwt_pair(api_client):
    register(api_client)

    response = verify(api_client, read_sent_code())

    assert response.status_code == 200
    body = response.json()
    assert body["is_new_user"] is True
    user = User.objects.get()
    assert user.is_email_verified is True
    assert AccessToken(body["access"])["user_id"] == str(user.pk)
    assert user.last_login is not None


def test_verify_accepts_the_email_in_any_letter_case(api_client):
    register(api_client)

    response = verify(api_client, read_sent_code(), email="ANNA@example.com")

    assert response.status_code == 200


def test_verify_code_works_once(api_client):
    register(api_client)
    code = read_sent_code()
    verify(api_client, code)

    response = verify(api_client, code)

    assert response.status_code == 400
    assert response.json()["code"] == "code_invalid"


def test_verify_counts_wrong_attempts(api_client):
    register(api_client)
    wrong_code = wrong_code_for(read_sent_code())

    response = verify(api_client, wrong_code)

    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "code_invalid"
    assert body["attempts_left"] == MAX_CODE_ATTEMPTS - 1
    assert User.objects.get().is_email_verified is False


def test_verify_refuses_the_right_code_after_too_many_attempts(api_client):
    register(api_client)
    code = read_sent_code()
    for _ in range(MAX_CODE_ATTEMPTS):
        verify(api_client, wrong_code_for(code))

    response = verify(api_client, code)

    assert response.status_code == 400
    assert response.json()["code"] == "code_attempts_exceeded"
    assert User.objects.get().is_email_verified is False


def test_verify_refuses_an_expired_code(api_client):
    register(api_client)
    code = read_sent_code()
    forget_cooldown()

    response = verify(api_client, code)

    assert response.status_code == 400
    assert response.json()["code"] == "code_expired"


@pytest.mark.parametrize("code", ["12345", "1234567", "abcdef", ""])
def test_verify_refuses_a_malformed_code(api_client, code):
    response = verify(api_client, code)

    assert response.status_code == 400
    assert response.json()["code"] == "validation_error"
    assert "code" in response.json()["fields"]


def test_verify_refuses_a_disabled_account(api_client):
    register(api_client)
    User.objects.update(is_active=False)

    response = verify(api_client, read_sent_code())

    assert response.status_code == 403
    assert response.json()["code"] == "account_disabled"
    assert User.objects.get().is_email_verified is False


# --- logging in ---


def test_login_is_refused_before_the_code_is_entered(api_client):
    register(api_client)

    response = log_in(api_client)

    assert response.status_code == 403
    assert response.json()["code"] == "email_not_verified"
    assert "access" not in response.json()


def test_login_works_after_the_code_is_entered(api_client):
    register(api_client)
    verify(api_client, read_sent_code())

    response = log_in(api_client, email="Anna@Example.com")

    assert response.status_code == 200
    body = response.json()
    assert body["is_new_user"] is False
    assert AccessToken(body["access"])["user_id"] == str(User.objects.get().pk)


def test_login_refuses_a_wrong_password(api_client):
    register(api_client)
    verify(api_client, read_sent_code())

    response = log_in(api_client, password="not-the-password")

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"


def test_login_answers_the_same_for_an_unknown_email(api_client):
    register(api_client)
    verify(api_client, read_sent_code())

    known_response = log_in(api_client, password="not-the-password")
    unknown_response = log_in(api_client, email="nobody@example.com")

    assert known_response.status_code == unknown_response.status_code == 401
    assert known_response.json() == unknown_response.json()


def test_login_does_not_tell_an_unverified_state_without_the_password(api_client):
    register(api_client)

    response = log_in(api_client, password="not-the-password")

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"


def test_login_refuses_a_user_without_a_password(api_client):
    User.objects.create_user("anna", email=EMAIL, is_email_verified=True)

    response = log_in(api_client)

    assert response.status_code == 401


def test_login_refuses_a_disabled_account(api_client):
    register(api_client)
    verify(api_client, read_sent_code())
    User.objects.update(is_active=False)

    response = log_in(api_client)

    assert response.status_code == 403
    assert response.json()["code"] == "account_disabled"


@pytest.mark.parametrize("body", [{}, {"email": EMAIL}, {"password": PASSWORD}])
def test_login_refuses_an_incomplete_body(api_client, body):
    response = api_client.post(LOGIN_URL, body, format="json")

    assert response.status_code == 400
    assert response.json()["code"] == "validation_error"


# --- asking for a new code ---


def test_unverified_user_can_ask_for_a_new_code(api_client):
    register(api_client)
    forget_cooldown()

    response = api_client.post(CODE_URL, {"email": EMAIL}, format="json")

    assert response.status_code == 200
    assert response.json() == {"resend_after_seconds": 60}
    assert len(mail.outbox) == 2
    assert verify(api_client, read_sent_code()).status_code == 200


def test_the_old_code_stops_working_after_a_new_one(api_client, monkeypatch):
    codes = iter(["111111", "222222"])
    monkeypatch.setattr(
        "apps.accounts.services.codes._generate_code",
        lambda: next(codes),
    )
    register(api_client)
    forget_cooldown()
    api_client.post(CODE_URL, {"email": EMAIL}, format="json")

    old_response = verify(api_client, "111111")
    new_response = verify(api_client, "222222")

    assert old_response.status_code == 400
    assert new_response.status_code == 200


def test_code_request_sends_nothing_to_an_unknown_email(api_client):
    response = api_client.post(CODE_URL, {"email": "nobody@example.com"}, format="json")

    assert response.status_code == 200
    assert response.json() == {"resend_after_seconds": 60}
    assert mail.outbox == []


def test_code_request_sends_nothing_to_a_confirmed_email(api_client):
    register(api_client)
    verify(api_client, read_sent_code())
    mail.outbox.clear()
    forget_cooldown()

    response = api_client.post(CODE_URL, {"email": EMAIL}, format="json")

    assert response.status_code == 200
    assert mail.outbox == []


def test_code_request_is_refused_during_the_resend_cooldown(api_client):
    register(api_client)

    response = api_client.post(CODE_URL, {"email": EMAIL}, format="json")

    assert response.status_code == 429
    assert response.json()["code"] == "code_resend_too_soon"


def test_code_request_refuses_an_invalid_email(api_client):
    response = api_client.post(CODE_URL, {"email": "nope"}, format="json")

    assert response.status_code == 400
    assert "email" in response.json()["fields"]


def test_code_requests_are_throttled_per_email(api_client):
    statuses = []
    for _ in range(7):
        forget_cooldown()
        response = api_client.post(CODE_URL, {"email": EMAIL}, format="json")
        statuses.append(response.status_code)

    assert statuses[:5] == [200] * 5
    assert set(statuses[5:]) == {429}
