from urllib.parse import parse_qs, urlparse

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.cache import cache
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from kombu.exceptions import OperationalError
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.tasks import PASSWORD_RESET_SUBJECT, send_password_reset_email

pytestmark = pytest.mark.django_db

FORGOT_URL = "/api/auth/password-forgot/"
RESET_URL = "/api/auth/password-reset/"
LOGIN_URL = "/api/auth/email-login/"
REFRESH_URL = "/api/auth/refresh/"
EMAIL = "anna@example.com"
OLD_PASSWORD = "correct-horse-battery"
NEW_PASSWORD = "another-long-password"
FRONTEND_URL = "https://app.freecook.example"


@pytest.fixture(autouse=True)
def isolated_environment(settings, monkeypatch):
    # Throttle counters must not leak between tests or into a real Redis.
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "password-reset-tests",
        },
    }
    settings.FRONTEND_URL = FRONTEND_URL
    cache.clear()
    # Run the task at once instead of sending it to a broker.
    monkeypatch.setattr(
        "apps.accounts.views.password.send_password_reset_email.delay",
        send_password_reset_email,
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return get_user_model().objects.create_user(
        nickname="anna",
        password=OLD_PASSWORD,
        email=EMAIL,
        is_email_verified=True,
    )


def ask_for_link(api_client, email=EMAIL):
    return api_client.post(FORGOT_URL, {"email": email}, format="json")


def read_link_parts():
    """Return (uid, token) from the link in the last letter."""
    link = next(
        word for word in mail.outbox[-1].body.split() if word.startswith("http")
    )
    query = parse_qs(urlparse(link).query)
    return query["uid"][0], query["token"][0]


def reset_password(api_client, uid, token, password=NEW_PASSWORD):
    body = {"uid": uid, "token": token, "password": password}
    return api_client.post(RESET_URL, body, format="json")


def log_in(api_client, password):
    body = {"email": EMAIL, "password": password}
    return api_client.post(LOGIN_URL, body, format="json")


# --- asking for a link ---


def test_forgot_emails_a_link_to_the_reset_page(api_client, user):
    response = ask_for_link(api_client)

    assert response.status_code == 200
    assert len(mail.outbox) == 1
    letter = mail.outbox[0]
    assert letter.to == [EMAIL]
    assert letter.subject == PASSWORD_RESET_SUBJECT
    link = next(word for word in letter.body.split() if word.startswith("http"))
    parsed = urlparse(link)
    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == (
        f"{FRONTEND_URL}/reset-password"
    )
    assert set(parse_qs(parsed.query)) == {"uid", "token"}


def test_forgot_letter_has_an_html_version_with_the_same_link(api_client, user):
    ask_for_link(api_client)

    letter = mail.outbox[0]
    link = next(word for word in letter.body.split() if word.startswith("http"))
    html, mimetype = letter.alternatives[0]
    assert mimetype == "text/html"
    assert link.replace("&", "&amp;") in html


def test_forgot_ignores_letter_case_of_the_email(api_client, user):
    ask_for_link(api_client, email="Anna@Example.com")

    assert len(mail.outbox) == 1


def test_forgot_answers_the_same_for_a_known_and_an_unknown_email(api_client, user):
    known_response = ask_for_link(api_client)
    unknown_response = ask_for_link(api_client, email="nobody@example.com")

    assert known_response.status_code == unknown_response.status_code == 200
    assert known_response.json() == unknown_response.json()


def test_forgot_sends_nothing_for_an_unknown_email(api_client):
    response = ask_for_link(api_client, email="nobody@example.com")

    assert response.status_code == 200
    assert mail.outbox == []


def test_forgot_sends_nothing_to_an_account_without_a_password(api_client):
    get_user_model().objects.create_user(
        nickname="phone_anna",
        email=EMAIL,
        is_email_verified=True,
    )

    response = ask_for_link(api_client)

    assert response.status_code == 200
    assert mail.outbox == []


def test_forgot_sends_nothing_when_the_email_is_not_confirmed(api_client, user):
    user.is_email_verified = False
    user.save()

    response = ask_for_link(api_client)

    assert response.status_code == 200
    assert mail.outbox == []


def test_forgot_sends_nothing_to_a_disabled_account(api_client, user):
    user.is_active = False
    user.save()

    response = ask_for_link(api_client)

    assert response.status_code == 200
    assert mail.outbox == []


def test_forgot_rejects_a_malformed_email(api_client):
    response = api_client.post(FORGOT_URL, {"email": "not-an-email"}, format="json")

    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "validation_error"
    assert "email" in body["fields"]


def test_forgot_limits_requests_for_one_email(api_client, user):
    statuses = [ask_for_link(api_client).status_code for _ in range(6)]

    assert statuses == [200, 200, 200, 200, 200, 429]


def test_forgot_limits_requests_for_an_unknown_email_the_same_way(api_client):
    statuses = [
        ask_for_link(api_client, email="nobody@example.com").status_code
        for _ in range(6)
    ]

    assert statuses == [200, 200, 200, 200, 200, 429]


def test_forgot_answers_the_same_when_the_broker_is_down(
    api_client,
    user,
    monkeypatch,
):
    def fail_to_queue(*args, **kwargs):
        raise OperationalError("Connection refused")

    monkeypatch.setattr(
        "apps.accounts.views.password.send_password_reset_email.delay",
        fail_to_queue,
    )

    response = ask_for_link(api_client)

    assert response.status_code == 200
    assert (
        response.json() == ask_for_link(api_client, email="nobody@example.com").json()
    )


# --- using the link ---


def test_reset_sets_a_new_password(api_client, user):
    ask_for_link(api_client)
    uid, token = read_link_parts()

    response = reset_password(api_client, uid, token)

    assert response.status_code == 200
    assert log_in(api_client, NEW_PASSWORD).status_code == 200
    assert log_in(api_client, OLD_PASSWORD).status_code == 401


def test_reset_link_works_only_once(api_client, user):
    ask_for_link(api_client)
    uid, token = read_link_parts()

    reset_password(api_client, uid, token)
    second_response = reset_password(api_client, uid, token, "third-long-password")

    assert second_response.status_code == 400
    assert second_response.json()["code"] == "reset_link_invalid"
    assert log_in(api_client, NEW_PASSWORD).status_code == 200


def test_reset_link_stops_working_after_an_hour(api_client, user, settings):
    ask_for_link(api_client)
    uid, token = read_link_parts()
    # An hour has passed: a timeout in the past is the same as an old link.
    settings.PASSWORD_RESET_TIMEOUT = -1

    response = reset_password(api_client, uid, token)

    assert response.status_code == 400
    assert response.json()["code"] == "reset_link_invalid"
    assert log_in(api_client, OLD_PASSWORD).status_code == 200


def test_reset_link_stops_working_when_the_password_changes_another_way(
    api_client,
    user,
):
    ask_for_link(api_client)
    uid, token = read_link_parts()
    user.set_password("changed-in-the-profile")
    user.save()

    response = reset_password(api_client, uid, token)

    assert response.status_code == 400
    assert response.json()["code"] == "reset_link_invalid"


def test_reset_rejects_a_wrong_token(api_client, user):
    ask_for_link(api_client)
    uid, _ = read_link_parts()

    response = reset_password(api_client, uid, "wrong-token")

    assert response.status_code == 400
    assert response.json()["code"] == "reset_link_invalid"


def test_reset_rejects_an_unknown_or_malformed_uid(api_client, user):
    ask_for_link(api_client)
    _, token = read_link_parts()

    for uid in [
        "not-base64!",
        "bm9wZQ",
        "MDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAw",
    ]:
        response = reset_password(api_client, uid, token)

        assert response.status_code == 400
        assert response.json()["code"] == "reset_link_invalid"


def test_reset_rejects_the_token_of_another_user(api_client, user):
    other_user = get_user_model().objects.create_user(
        nickname="olga",
        password=OLD_PASSWORD,
        email="olga@example.com",
        is_email_verified=True,
    )
    ask_for_link(api_client, email="olga@example.com")
    _, other_token = read_link_parts()
    ask_for_link(api_client)
    uid, _ = read_link_parts()

    response = reset_password(api_client, uid, other_token)

    assert response.status_code == 400
    other_user.refresh_from_db()
    assert other_user.check_password(OLD_PASSWORD)


def test_reset_refuses_an_account_without_a_password(api_client):
    phone_user = get_user_model().objects.create_user(
        nickname="phone_anna",
        phone="+380501234567",
    )
    uid = urlsafe_base64_encode(force_bytes(phone_user.pk))
    token = default_token_generator.make_token(phone_user)

    response = reset_password(api_client, uid, token)

    assert response.status_code == 400
    assert response.json()["code"] == "reset_link_invalid"
    phone_user.refresh_from_db()
    assert phone_user.has_usable_password() is False


def test_reset_rejects_a_weak_password_and_keeps_the_link_alive(api_client, user):
    ask_for_link(api_client)
    uid, token = read_link_parts()

    weak_response = reset_password(api_client, uid, token, "12345678")
    good_response = reset_password(api_client, uid, token)

    assert weak_response.status_code == 400
    body = weak_response.json()
    assert body["code"] == "validation_error"
    assert body["fields"]["password"]
    assert good_response.status_code == 200


def test_reset_requires_all_fields(api_client):
    response = api_client.post(RESET_URL, {}, format="json")

    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "validation_error"
    assert set(body["fields"]) == {"uid", "token", "password"}


def test_reset_logs_out_every_device(api_client, user):
    refresh = RefreshToken.for_user(user)
    ask_for_link(api_client)
    uid, token = read_link_parts()

    reset_password(api_client, uid, token)
    response = api_client.post(REFRESH_URL, {"refresh": str(refresh)}, format="json")

    assert response.status_code == 401
