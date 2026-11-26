from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

pytestmark = pytest.mark.django_db

REFRESH_URL = "/api/auth/refresh/"
LOGOUT_URL = "/api/auth/logout/"
ME_URL = "/api/me/"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return get_user_model().objects.create_user(
        nickname="anna",
        email="anna@example.com",
    )


def authorize(api_client, user):
    access = str(RefreshToken.for_user(user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return api_client


def post_refresh(api_client, token):
    return api_client.post(REFRESH_URL, {"refresh": str(token)}, format="json")


def post_logout(api_client, token):
    return api_client.post(LOGOUT_URL, {"refresh": str(token)}, format="json")


# --- token lifetimes ---


def test_access_token_lives_15_minutes(user):
    access = RefreshToken.for_user(user).access_token

    assert access["exp"] - access["iat"] == timedelta(minutes=15).total_seconds()


def test_refresh_token_lives_30_days(user):
    refresh = RefreshToken.for_user(user)

    assert refresh["exp"] - refresh["iat"] == timedelta(days=30).total_seconds()


def test_issued_refresh_token_is_tracked_for_revocation(user):
    refresh = RefreshToken.for_user(user)

    assert OutstandingToken.objects.filter(jti=refresh["jti"], user=user).exists()


# --- refreshing ---


def test_refresh_returns_a_new_pair(api_client, user):
    old_refresh = RefreshToken.for_user(user)

    response = post_refresh(api_client, old_refresh)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"refresh", "access"}
    assert body["refresh"] != str(old_refresh)
    assert AccessToken(body["access"])["user_id"] == str(user.pk)


def test_refresh_revokes_the_token_that_was_sent(api_client, user):
    old_refresh = RefreshToken.for_user(user)

    post_refresh(api_client, old_refresh)
    second_response = post_refresh(api_client, old_refresh)

    assert second_response.status_code == 401
    assert second_response.json()["code"] == "session_ended"
    assert BlacklistedToken.objects.filter(token__jti=old_refresh["jti"]).exists()


def test_refresh_token_from_a_refresh_can_be_used_again(api_client, user):
    first_body = post_refresh(api_client, RefreshToken.for_user(user)).json()

    second_response = post_refresh(api_client, first_body["refresh"])

    assert second_response.status_code == 200


def test_refresh_does_not_change_last_login(api_client, user):
    post_refresh(api_client, RefreshToken.for_user(user))

    user.refresh_from_db()
    assert user.last_login is None


def test_refresh_rejects_garbage(api_client):
    response = post_refresh(api_client, "not-a-token")

    assert response.status_code == 401
    assert response.json()["code"] == "session_ended"


def test_refresh_rejects_an_access_token(api_client, user):
    access = RefreshToken.for_user(user).access_token

    response = post_refresh(api_client, access)

    assert response.status_code == 401


def test_refresh_rejects_an_expired_token(api_client, user):
    refresh = RefreshToken.for_user(user)
    refresh.set_exp(lifetime=-timedelta(seconds=1))

    response = post_refresh(api_client, refresh)

    assert response.status_code == 401


def test_refresh_requires_the_token(api_client):
    response = api_client.post(REFRESH_URL, {}, format="json")

    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "validation_error"
    assert "refresh" in body["fields"]


def test_refresh_refuses_a_disabled_account(api_client, user):
    refresh = RefreshToken.for_user(user)
    user.is_active = False
    user.save()

    response = post_refresh(api_client, refresh)

    assert response.status_code == 403
    assert response.json()["code"] == "account_disabled"


# --- logging out ---


def test_logout_makes_the_refresh_token_unusable(api_client, user):
    refresh = RefreshToken.for_user(user)

    logout_response = post_logout(api_client, refresh)
    refresh_response = post_refresh(api_client, refresh)

    assert logout_response.status_code == 204
    assert refresh_response.status_code == 401


def test_logout_twice_is_still_a_success(api_client, user):
    refresh = RefreshToken.for_user(user)

    post_logout(api_client, refresh)
    second_response = post_logout(api_client, refresh)

    assert second_response.status_code == 204


def test_logout_with_an_unknown_token_is_a_success(api_client):
    response = post_logout(api_client, "not-a-token")

    assert response.status_code == 204


def test_logout_does_not_touch_other_sessions(api_client, user):
    this_device = RefreshToken.for_user(user)
    other_device = RefreshToken.for_user(user)

    post_logout(api_client, this_device)

    assert post_refresh(api_client, other_device).status_code == 200


def test_logout_requires_the_token(api_client):
    response = api_client.post(LOGOUT_URL, {}, format="json")

    assert response.status_code == 400
    assert response.json()["code"] == "validation_error"


# --- the current user ---


def test_me_requires_a_login(api_client):
    response = api_client.get(ME_URL)

    assert response.status_code == 401


def test_me_returns_the_current_user(api_client, user):
    user.phone = "+380501234567"
    user.name = "Анна"
    user.save()

    response = authorize(api_client, user).get(ME_URL)

    assert response.status_code == 200
    assert response.json() == {
        "id": str(user.pk),
        "email": "anna@example.com",
        "phone": "+380501234567",
        "is_telegram_linked": False,
        "is_email_verified": False,
        "name": "Анна",
        "nickname": "anna",
        "gender": "unset",
        "theme_color": "white",
        "is_onboarding_done": False,
    }


def test_me_shows_a_linked_telegram_account(api_client, user):
    user.telegram_id = 123456789
    user.save()

    body = authorize(api_client, user).get(ME_URL).json()

    assert body["is_telegram_linked"] is True
    assert "telegram_id" not in body


def test_me_updates_theme_color_and_onboarding(api_client, user):
    response = authorize(api_client, user).patch(
        ME_URL,
        {"theme_color": "ocean", "is_onboarding_done": True},
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["theme_color"] == "ocean"
    assert response.json()["is_onboarding_done"] is True
    user.refresh_from_db()
    assert user.theme_color == "ocean"
    assert user.is_onboarding_done is True


def test_me_update_keeps_fields_that_were_not_sent(api_client, user):
    user.name = "Анна"
    user.save()

    authorize(api_client, user).patch(ME_URL, {"theme_color": "sky"}, format="json")

    user.refresh_from_db()
    assert user.name == "Анна"
    assert user.theme_color == "sky"


def test_me_updates_name_nickname_and_gender(api_client, user):
    response = authorize(api_client, user).patch(
        ME_URL,
        {"name": "Анна", "nickname": "anna_k", "gender": "female"},
        format="json",
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert (user.name, user.nickname, user.gender) == ("Анна", "anna_k", "female")


def test_me_rejects_an_unknown_theme_color(api_client, user):
    response = authorize(api_client, user).patch(
        ME_URL,
        {"theme_color": "green"},
        format="json",
    )

    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "validation_error"
    assert "theme_color" in body["fields"]


def test_me_rejects_a_nickname_that_is_taken(api_client, user):
    get_user_model().objects.create_user(nickname="taken", phone="+380671112233")

    response = authorize(api_client, user).patch(
        ME_URL,
        {"nickname": "taken"},
        format="json",
    )

    assert response.status_code == 400
    assert "nickname" in response.json()["fields"]


def test_me_ignores_contacts_and_verification(api_client, user):
    response = authorize(api_client, user).patch(
        ME_URL,
        {
            "email": "other@example.com",
            "phone": "+380509998877",
            "is_email_verified": True,
        },
        format="json",
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.email == "anna@example.com"
    assert user.phone is None
    assert user.is_email_verified is False


def test_me_does_not_accept_put(api_client, user):
    response = authorize(api_client, user).put(
        ME_URL,
        {"nickname": "anna"},
        format="json",
    )

    assert response.status_code == 405
