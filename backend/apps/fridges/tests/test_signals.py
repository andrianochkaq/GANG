import pytest

from apps.accounts.models import User
from apps.accounts.services.email_accounts import register_email_user
from apps.fridges.models import Fridge, FridgeMembership, FridgeRole, MembershipStatus
from apps.fridges.services import DEFAULT_FRIDGE_NAME

pytestmark = pytest.mark.django_db


def assert_has_one_default_fridge(user):
    fridges = Fridge.objects.filter(owner=user)
    assert fridges.count() == 1
    assert fridges.get().name == DEFAULT_FRIDGE_NAME
    membership = FridgeMembership.objects.get(user=user)
    assert membership.fridge == fridges.get()
    assert membership.role == FridgeRole.OWNER
    assert membership.status == MembershipStatus.ACTIVE


def test_email_registration_creates_one_default_fridge():
    user = register_email_user("anna@example.com", "correct-horse-battery")

    assert_has_one_default_fridge(user)


@pytest.mark.parametrize(
    "contact",
    [{"phone": "+380501234567"}, {"telegram_id": 123456789}],
    ids=["phone", "telegram_id"],
)
def test_phone_and_telegram_registration_create_one_default_fridge(contact):
    user = User.objects.create_user("anna", **contact)

    assert_has_one_default_fridge(user)


def test_saving_an_existing_user_does_not_create_another_fridge():
    user = User.objects.create_user("anna", email="anna@example.com")

    user.name = "Анна"
    user.save()

    assert_has_one_default_fridge(user)
