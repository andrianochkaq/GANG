import pytest
from django.contrib.auth.validators import UnicodeUsernameValidator

from apps.accounts.models import OneTimeCode, User
from apps.accounts.services.email_auth import (
    NICKNAME_BASE_MAX_LENGTH,
    NICKNAME_FALLBACK,
    start_email_registration,
)

pytestmark = pytest.mark.django_db

PASSWORD = "pear-lamp-violet-92"


def register_nickname(email):
    start_email_registration(email, PASSWORD)
    return User.objects.get(email=email).nickname


def test_nickname_is_the_name_part_of_the_email():
    assert register_nickname("anna@example.com") == "anna"


def test_nickname_drops_characters_a_nickname_cannot_have():
    assert register_nickname("an!na#tag+x@example.com") == "annatag+x"


def test_nickname_is_cut_to_a_short_base():
    long_name = "a" * 40

    nickname = register_nickname(f"{long_name}@example.com")

    assert nickname == "a" * NICKNAME_BASE_MAX_LENGTH


def test_nickname_has_a_fallback_when_nothing_is_left():
    assert register_nickname("!!!@example.com") == NICKNAME_FALLBACK


def test_taken_nickname_gets_a_number():
    User.objects.create_user("anna", phone="+380501234567")

    nickname = register_nickname("anna@example.com")

    assert nickname.startswith("anna")
    assert nickname != "anna"
    assert len(nickname) <= User._meta.get_field("nickname").max_length
    UnicodeUsernameValidator()(nickname)


def test_registration_keeps_only_a_hash_of_the_code():
    code = start_email_registration("anna@example.com", PASSWORD)

    assert OneTimeCode.objects.get().code_hash != code
