import pytest
from django.db import IntegrityError, transaction

from apps.accounts.models import User
from apps.fridges.models import (
    Fridge,
    FridgeMembership,
    FridgeRole,
    MembershipStatus,
)
from apps.fridges.services import create_fridge

pytestmark = pytest.mark.django_db


def make_user(nickname):
    return User.objects.create_user(nickname, email=f"{nickname}@example.com")


def test_create_fridge_makes_the_owner_an_active_owner_member():
    owner = make_user("anna")

    fridge = create_fridge(owner, "Дача")

    membership = FridgeMembership.objects.get(fridge=fridge, user=owner)
    assert fridge.owner == owner
    assert membership.role == FridgeRole.OWNER
    assert membership.status == MembershipStatus.ACTIVE


def test_new_membership_is_a_pending_member_by_default():
    fridge = create_fridge(make_user("anna"), "Дача")
    guest = make_user("olga")

    membership = FridgeMembership.objects.create(fridge=fridge, user=guest)

    assert membership.role == FridgeRole.MEMBER
    assert membership.status == MembershipStatus.PENDING


def test_a_user_cannot_join_the_same_fridge_twice():
    fridge = create_fridge(make_user("anna"), "Дача")
    guest = make_user("olga")
    FridgeMembership.objects.create(fridge=fridge, user=guest)

    with pytest.raises(IntegrityError), transaction.atomic():
        FridgeMembership.objects.create(fridge=fridge, user=guest)


def test_visible_to_returns_only_fridges_of_active_members():
    anna = make_user("anna")
    olga = make_user("olga")
    shared_fridge = create_fridge(anna, "Спільний")
    pending_fridge = create_fridge(anna, "Очікування")
    FridgeMembership.objects.create(
        fridge=shared_fridge,
        user=olga,
        status=MembershipStatus.ACTIVE,
    )
    FridgeMembership.objects.create(fridge=pending_fridge, user=olga)

    visible_fridges = set(Fridge.objects.visible_to(olga))

    assert shared_fridge in visible_fridges
    assert pending_fridge not in visible_fridges
    assert len(visible_fridges) == 2  # also her own default fridge
