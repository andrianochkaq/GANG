import pytest
from django.urls import reverse

from apps.accounts.models import User

TEST_PASSWORD = "correct-horse-battery-staple"


@pytest.fixture
def admin_session(client):
    superuser = User.objects.create_superuser(
        "root",
        password=TEST_PASSWORD,
        email="root@example.com",
    )
    client.force_login(superuser)
    return client


def build_user_form(**overrides):
    form = {
        "nickname": "anna",
        "name": "",
        "gender": "unset",
        "email": "",
        "phone": "",
        "telegram_id": "",
        "password1": "",
        "password2": "",
    }
    form.update(overrides)
    return form


@pytest.mark.django_db
@pytest.mark.parametrize(
    "contact",
    [
        {"email": "anna@example.com"},
        {"phone": "+380501234567"},
        {"telegram_id": "123456789"},
    ],
    ids=["email", "phone", "telegram_id"],
)
def test_admin_creates_a_user_of_each_kind(admin_session, contact):
    response = admin_session.post(
        reverse("admin:accounts_user_add"),
        build_user_form(**contact),
    )

    assert response.status_code == 302
    user = User.objects.get(nickname="anna")
    assert user.has_usable_password() is False
    for field_name, value in contact.items():
        assert str(getattr(user, field_name)) == value


@pytest.mark.django_db
def test_admin_creates_a_user_with_a_password(admin_session):
    response = admin_session.post(
        reverse("admin:accounts_user_add"),
        build_user_form(
            email="anna@example.com",
            password1=TEST_PASSWORD,
            password2=TEST_PASSWORD,
        ),
    )

    assert response.status_code == 302
    assert User.objects.get(nickname="anna").check_password(TEST_PASSWORD) is True


@pytest.mark.django_db
def test_admin_refuses_a_user_without_any_contact(admin_session):
    response = admin_session.post(
        reverse("admin:accounts_user_add"),
        build_user_form(),
    )

    assert response.status_code == 200
    assert not User.objects.filter(nickname="anna").exists()


@pytest.mark.django_db
def test_admin_refuses_mismatching_passwords(admin_session):
    response = admin_session.post(
        reverse("admin:accounts_user_add"),
        build_user_form(
            email="anna@example.com",
            password1=TEST_PASSWORD,
            password2="another-passphrase-entirely",
        ),
    )

    assert response.status_code == 200
    assert not User.objects.filter(nickname="anna").exists()


@pytest.mark.django_db
def test_admin_pages_open(admin_session):
    user = User.objects.create_user("anna", telegram_id=123456789)

    list_response = admin_session.get(reverse("admin:accounts_user_changelist"))
    add_response = admin_session.get(reverse("admin:accounts_user_add"))
    change_response = admin_session.get(
        reverse("admin:accounts_user_change", args=[user.pk]),
    )

    assert list_response.status_code == 200
    assert add_response.status_code == 200
    assert change_response.status_code == 200
