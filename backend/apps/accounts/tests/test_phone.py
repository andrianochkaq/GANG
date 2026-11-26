import re
from datetime import timedelta

import pytest
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import CodePurpose, OneTimeCode, User
from apps.accounts.serializers import PhoneLoginSerializer
from apps.accounts.services.codes import MAX_CODE_ATTEMPTS, issue_code
from core.sms import LocMemSmsBackend, SmsBackend, SmsError

pytestmark = pytest.mark.django_db

REQUEST_URL = "/api/auth/phone-code/"
LOGIN_URL = "/api/auth/phone-login/"
PHONE_NUMBER = "+380501234567"
OTHER_PHONE_NUMBER = "+380671234567"


class FailingSmsBackend(SmsBackend):
    def send_message(self, phone_number, text):
        raise SmsError("The provider is down.")


@pytest.fixture(autouse=True)
def isolated_environment(settings):
    # Throttle counters must not leak between tests or into a real Redis.
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "phone-login-tests",
        },
    }
    settings.SMS_BACKEND = "core.sms.LocMemSmsBackend"
    cache.clear()
    LocMemSmsBackend.outbox.clear()


@pytest.fixture
def api_client():
    return APIClient()


def request_code(api_client, phone=PHONE_NUMBER):
    return api_client.post(REQUEST_URL, {"phone": phone}, format="json")


def log_in(api_client, code, phone=PHONE_NUMBER):
    body = {"phone": phone, "code": code}
    return api_client.post(LOGIN_URL, body, format="json")


def read_sent_code():
    return re.search(r"[0-9]{6}", LocMemSmsBackend.outbox[-1].text).group()


def issue_login_code(phone=PHONE_NUMBER):
    # Earlier codes are removed so the resend cooldown does not get in the way.
    OneTimeCode.objects.all().delete()
    return issue_code(CodePurpose.PHONE_LOGIN, phone)


def wrong_code_for(code):
    return "000000" if code != "000000" else "111111"


# --- requesting a code ---


def test_request_sends_one_sms_with_a_code(api_client):
    response = request_code(api_client)

    assert response.status_code == 200
    assert response.json() == {"resend_after_seconds": 60}
    assert len(LocMemSmsBackend.outbox) == 1
    assert LocMemSmsBackend.outbox[0].phone_number == PHONE_NUMBER
    assert len(read_sent_code()) == 6


def test_request_sends_to_the_normalized_number(api_client):
    response = request_code(api_client, "050 123 45 67")

    assert response.status_code == 200
    assert LocMemSmsBackend.outbox[0].phone_number == PHONE_NUMBER


def test_request_does_not_put_the_number_into_the_message(api_client):
    request_code(api_client)

    assert PHONE_NUMBER not in LocMemSmsBackend.outbox[0].text


@pytest.mark.parametrize("body", [{"phone": "12345"}, {"phone": ""}, {}])
def test_request_refuses_an_invalid_number(api_client, body):
    response = api_client.post(REQUEST_URL, body, format="json")

    assert response.status_code == 400
    assert response.json()["code"] == "validation_error"
    assert "phone" in response.json()["fields"]
    assert LocMemSmsBackend.outbox == []
    assert OneTimeCode.objects.count() == 0


def test_request_answers_the_same_for_known_and_new_numbers(api_client):
    User.objects.create_user("anna", phone=PHONE_NUMBER)

    known_response = request_code(api_client, PHONE_NUMBER)
    new_response = request_code(api_client, OTHER_PHONE_NUMBER)

    assert known_response.status_code == new_response.status_code == 200
    assert known_response.json() == new_response.json()


def test_request_is_refused_during_the_resend_cooldown(api_client):
    request_code(api_client)

    response = request_code(api_client)

    assert response.status_code == 429
    body = response.json()
    assert body["code"] == "code_resend_too_soon"
    assert 1 <= body["retry_after_seconds"] <= 60
    assert response["Retry-After"] == str(body["retry_after_seconds"])
    assert len(LocMemSmsBackend.outbox) == 1


def test_request_is_throttled_per_ip_address(api_client):
    statuses = [
        request_code(api_client, f"+38050123456{digit}").status_code
        for digit in range(6)
    ]

    assert statuses == [200, 200, 200, 200, 200, 429]
    assert len(LocMemSmsBackend.outbox) == 5


def test_request_reports_an_unavailable_provider(api_client, settings):
    settings.SMS_BACKEND = "apps.accounts.tests.test_phone.FailingSmsBackend"

    response = request_code(api_client)

    assert response.status_code == 503
    assert response.json()["code"] == "sms_unavailable"


# --- logging in with a code ---


def test_login_creates_an_account_for_a_new_number(api_client):
    code = issue_login_code()

    response = log_in(api_client, code)

    assert response.status_code == 200
    body = response.json()
    assert body["is_new_user"] is True
    user = User.objects.get(phone=PHONE_NUMBER)
    assert AccessToken(body["access"])["user_id"] == str(user.pk)
    assert body["refresh"]


def test_login_after_an_sms_request_works_end_to_end(api_client):
    request_code(api_client)

    response = log_in(api_client, read_sent_code())

    assert response.status_code == 200
    assert User.objects.filter(phone=PHONE_NUMBER).count() == 1


def test_same_number_always_logs_into_the_same_account(api_client):
    first_response = log_in(api_client, issue_login_code())
    second_response = log_in(api_client, issue_login_code())

    first_user_id = AccessToken(first_response.json()["access"])["user_id"]
    second_user_id = AccessToken(second_response.json()["access"])["user_id"]
    assert first_response.json()["is_new_user"] is True
    assert second_response.json()["is_new_user"] is False
    assert first_user_id == second_user_id
    assert User.objects.filter(phone=PHONE_NUMBER).count() == 1


def test_number_written_differently_logs_into_the_same_account(api_client):
    first_response = log_in(api_client, issue_login_code())
    second_response = log_in(api_client, issue_login_code(), "050 123 45 67")

    assert second_response.status_code == 200
    first_user_id = AccessToken(first_response.json()["access"])["user_id"]
    second_user_id = AccessToken(second_response.json()["access"])["user_id"]
    assert first_user_id == second_user_id
    assert User.objects.count() == 1


def test_login_never_asks_for_a_password(api_client):
    response = log_in(api_client, issue_login_code())

    user = User.objects.get(phone=PHONE_NUMBER)
    assert response.status_code == 200
    assert "password" not in PhoneLoginSerializer().fields
    assert user.has_usable_password() is False


def test_login_updates_the_last_login_time(api_client):
    started_at = timezone.now()

    log_in(api_client, issue_login_code())

    assert User.objects.get(phone=PHONE_NUMBER).last_login >= started_at


def test_login_refuses_a_wrong_code_and_counts_the_attempt(api_client):
    code = issue_login_code()

    response = log_in(api_client, wrong_code_for(code))

    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "code_invalid"
    assert body["attempts_left"] == MAX_CODE_ATTEMPTS - 1
    assert User.objects.count() == 0


def test_login_refuses_a_number_that_asked_for_no_code(api_client):
    response = log_in(api_client, "123456")

    assert response.status_code == 400
    assert response.json()["code"] == "code_invalid"
    assert User.objects.count() == 0


def test_code_of_one_number_does_not_log_into_another(api_client):
    code = issue_login_code(PHONE_NUMBER)

    response = log_in(api_client, code, OTHER_PHONE_NUMBER)

    assert response.status_code == 400
    assert User.objects.count() == 0


@pytest.mark.parametrize("code", ["12ab56", "12345", "1234567", ""])
def test_login_refuses_a_malformed_code(api_client, code):
    response = log_in(api_client, code)

    assert response.status_code == 400
    assert response.json()["code"] == "validation_error"
    assert "code" in response.json()["fields"]


def test_login_refuses_an_invalid_number(api_client):
    response = log_in(api_client, "123456", "12345")

    assert response.status_code == 400
    assert "phone" in response.json()["fields"]


def test_login_refuses_an_expired_code(api_client):
    code = issue_login_code()
    OneTimeCode.objects.update(expires_at=timezone.now() - timedelta(minutes=1))

    response = log_in(api_client, code)

    assert response.status_code == 400
    assert response.json()["code"] == "code_expired"
    assert User.objects.count() == 0


def test_login_refuses_the_right_code_after_too_many_wrong_ones(api_client):
    code = issue_login_code()
    for _ in range(MAX_CODE_ATTEMPTS):
        log_in(api_client, wrong_code_for(code))

    response = log_in(api_client, code)

    assert response.status_code == 400
    assert response.json()["code"] == "code_attempts_exceeded"
    assert User.objects.count() == 0


def test_code_works_only_once(api_client):
    code = issue_login_code()
    log_in(api_client, code)

    response = log_in(api_client, code)

    assert response.status_code == 400
    assert response.json()["code"] == "code_invalid"


def test_login_refuses_a_disabled_account(api_client):
    User.objects.create_user("anna", phone=PHONE_NUMBER, is_active=False)

    response = log_in(api_client, issue_login_code())

    assert response.status_code == 403
    body = response.json()
    assert body["code"] == "account_disabled"
    assert "access" not in body
    assert "refresh" not in body
