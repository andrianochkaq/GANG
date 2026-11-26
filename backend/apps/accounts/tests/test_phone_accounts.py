import pytest
from django.contrib.auth.validators import UnicodeUsernameValidator

from apps.accounts.models import User
from apps.accounts.services.phone_accounts import (
    NICKNAME_PREFIX,
    get_or_create_phone_user,
)

pytestmark = pytest.mark.django_db

PHONE_NUMBER = "+380501234567"
OTHER_PHONE_NUMBER = "+380671234567"


def test_unknown_number_gets_a_new_account():
    user, is_created = get_or_create_phone_user(PHONE_NUMBER)

    assert is_created is True
    assert user.phone == PHONE_NUMBER
    assert User.objects.count() == 1


def test_known_number_gets_the_same_account():
    first_user, _ = get_or_create_phone_user(PHONE_NUMBER)

    second_user, is_created = get_or_create_phone_user(PHONE_NUMBER)

    assert is_created is False
    assert second_user.pk == first_user.pk
    assert User.objects.count() == 1


def test_new_account_has_no_password():
    user, _ = get_or_create_phone_user(PHONE_NUMBER)

    user.refresh_from_db()
    assert user.password is None
    assert user.has_usable_password() is False
    assert user.check_password("") is False


def test_new_account_has_no_email_and_is_not_onboarded():
    user, _ = get_or_create_phone_user(PHONE_NUMBER)

    assert user.email is None
    assert user.is_onboarding_done is False


def test_nickname_is_valid_and_does_not_reveal_the_number():
    user, _ = get_or_create_phone_user(PHONE_NUMBER)

    UnicodeUsernameValidator()(user.nickname)
    assert user.nickname.startswith(NICKNAME_PREFIX)
    assert len(user.nickname) <= User._meta.get_field("nickname").max_length
    assert PHONE_NUMBER.removeprefix("+") not in user.nickname


def test_different_numbers_get_different_accounts():
    first_user, _ = get_or_create_phone_user(PHONE_NUMBER)
    second_user, _ = get_or_create_phone_user(OTHER_PHONE_NUMBER)

    assert first_user.pk != second_user.pk
    assert first_user.nickname != second_user.nickname
