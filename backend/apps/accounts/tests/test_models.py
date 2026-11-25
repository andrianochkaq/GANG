import io

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction

from apps.accounts.models import Gender, ThemeColor, User

TEST_PASSWORD = "correct-horse-battery-staple"

CONTACT_KINDS = [
    {"email": "anna@example.com"},
    {"phone": "+380501234567"},
    {"telegram_id": 123456789},
]
CONTACT_KIND_IDS = ["email", "phone", "telegram_id"]


def test_user_model_is_the_project_user_model():
    assert get_user_model() is User


@pytest.mark.django_db
@pytest.mark.parametrize("contact", CONTACT_KINDS, ids=CONTACT_KIND_IDS)
def test_user_can_be_created_with_a_single_contact(contact):
    user = User.objects.create_user("anna", **contact)

    user.refresh_from_db()
    for field_name, value in contact.items():
        assert getattr(user, field_name) == value


@pytest.mark.django_db
def test_new_user_has_default_values():
    user = User.objects.create_user("anna", email="anna@example.com")

    user.refresh_from_db()
    assert user.password is None
    assert user.gender == Gender.UNSET
    assert user.theme_color == ThemeColor.WHITE
    assert user.is_onboarding_done is False
    assert user.is_email_verified is False
    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.is_active is True


@pytest.mark.django_db
def test_user_without_any_contact_is_refused_by_database():
    with pytest.raises(IntegrityError) as error, transaction.atomic():
        User.objects.create(nickname="ghost")

    assert "accounts_user_has_contact" in str(error.value)


@pytest.mark.django_db
def test_blank_contacts_are_refused_by_database():
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.bulk_create([User(nickname="ghost", email="", phone="")])


@pytest.mark.django_db
def test_blank_contact_is_saved_as_null():
    user = User.objects.create_user(
        "anna",
        email="  ",
        phone="+380501234567",
    )

    user.refresh_from_db()
    assert user.email is None


@pytest.mark.django_db
def test_users_without_an_email_do_not_clash():
    User.objects.create_user("anna", phone="+380501234567")
    User.objects.create_user("boris", phone="+380507654321")

    assert User.objects.filter(email__isnull=True).count() == 2


@pytest.mark.django_db
@pytest.mark.parametrize("contact", CONTACT_KINDS, ids=CONTACT_KIND_IDS)
def test_contact_must_be_unique(contact):
    User.objects.create_user("anna", **contact)

    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user("boris", **contact)


@pytest.mark.django_db
def test_nickname_must_be_unique():
    User.objects.create_user("anna", email="anna@example.com")

    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user("anna", email="other@example.com")


def test_clean_refuses_user_without_contact():
    user = User(nickname="ghost")

    with pytest.raises(ValidationError) as error:
        user.clean()

    assert error.value.code == "contact_required"


@pytest.mark.django_db
def test_full_clean_accepts_phone_in_e164_format():
    User(nickname="anna", phone="+380501234567").full_clean()


@pytest.mark.django_db
@pytest.mark.parametrize("phone", ["0501234567", "+0501234567", "+38 050 123", "+"])
def test_full_clean_refuses_phone_outside_e164_format(phone):
    user = User(nickname="anna", phone=phone)

    with pytest.raises(ValidationError) as error:
        user.full_clean()

    assert "phone" in error.value.message_dict


@pytest.mark.django_db
def test_user_without_password_cannot_log_in_with_a_password():
    user = User.objects.create_user("anna", email="anna@example.com")

    assert user.has_usable_password() is False
    assert user.check_password("") is False
    assert user.check_password(TEST_PASSWORD) is False


@pytest.mark.django_db
def test_user_with_password_can_log_in_with_it():
    user = User.objects.create_user(
        "anna",
        password=TEST_PASSWORD,
        email="anna@example.com",
    )

    assert user.has_usable_password() is True
    assert user.check_password(TEST_PASSWORD) is True
    assert user.check_password("wrong-password") is False


@pytest.mark.django_db
def test_superuser_is_staff_and_has_a_password():
    user = User.objects.create_superuser(
        "root",
        password=TEST_PASSWORD,
        email="root@example.com",
    )

    assert user.is_staff is True
    assert user.is_superuser is True
    assert user.check_password(TEST_PASSWORD) is True


@pytest.mark.django_db
def test_superuser_without_password_is_refused():
    with pytest.raises(ValueError):
        User.objects.create_superuser("root", email="root@example.com")


@pytest.mark.django_db
def test_user_without_nickname_is_refused():
    with pytest.raises(ValueError):
        User.objects.create_user("", email="anna@example.com")


def test_theme_color_has_the_17_design_system_colors():
    assert len(ThemeColor.choices) == 17
    assert ThemeColor.values[0] == "white"


def test_gender_choices_are_female_male_and_not_set():
    assert Gender.values == ["female", "male", "unset"]


def test_user_is_shown_by_nickname():
    assert str(User(nickname="anna")) == "anna"


@pytest.mark.django_db
def test_model_changes_have_migrations():
    call_command("makemigrations", "--check", "--dry-run", stdout=io.StringIO())
