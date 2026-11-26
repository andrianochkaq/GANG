import pytest

from apps.accounts.models import User
from apps.accounts.services.email_accounts import (
    confirm_email,
    find_user_by_email,
    register_email_user,
)

pytestmark = pytest.mark.django_db

EMAIL = "anna@example.com"
PASSWORD = "correct-horse-battery"


def test_register_creates_an_unverified_user_with_a_password():
    user = register_email_user(EMAIL, PASSWORD)

    assert user.email == EMAIL
    assert user.is_email_verified is False
    assert user.check_password(PASSWORD)
    assert user.nickname.startswith("user_")
    assert EMAIL not in user.nickname


def test_register_replaces_the_password_of_an_unverified_user():
    first_user = register_email_user(EMAIL, PASSWORD)

    second_user = register_email_user(EMAIL, "another-long-password")

    assert second_user.pk == first_user.pk
    assert second_user.check_password("another-long-password")
    assert not second_user.check_password(PASSWORD)
    assert User.objects.count() == 1


def test_register_keeps_a_verified_user_untouched():
    user = register_email_user(EMAIL, PASSWORD)
    confirm_email(user)

    result = register_email_user(EMAIL, "another-long-password")

    assert result is None
    user.refresh_from_db()
    assert user.check_password(PASSWORD)


def test_find_user_ignores_letter_case():
    user = register_email_user(EMAIL, PASSWORD)

    assert find_user_by_email("Anna@Example.com") == user
    assert find_user_by_email("nobody@example.com") is None


def test_confirm_email_marks_the_user():
    user = register_email_user(EMAIL, PASSWORD)

    confirm_email(user)

    user.refresh_from_db()
    assert user.is_email_verified is True
