import pytest

from apps.accounts.models import User
from apps.fridges.models import Fridge, FridgeMembership, MembershipStatus
from apps.fridges.services import (
    FridgeHasMembersError,
    OwnerCannotLeaveError,
    annotate_fridge_summary,
    create_fridge,
    delete_fridge,
    find_current_fridge_id,
    leave_fridge,
    select_fridge,
)

pytestmark = pytest.mark.django_db


def make_user(nickname):
    return User.objects.create_user(nickname, email=f"{nickname}@example.com")


def add_member(fridge, user, status=MembershipStatus.ACTIVE):
    return FridgeMembership.objects.create(fridge=fridge, user=user, status=status)


@pytest.fixture
def owner():
    return make_user("anna")


@pytest.fixture
def fridge(owner):
    return create_fridge(owner, "Дача")


# --- the summary of a fridge ---


def test_summary_counts_active_members_only(fridge, owner):
    add_member(fridge, make_user("olga"))
    add_member(fridge, make_user("petro"), status=MembershipStatus.PENDING)

    summary = annotate_fridge_summary(Fridge.objects.visible_to(owner)).get(
        pk=fridge.pk
    )

    assert summary.member_count == 2
    assert summary.product_count == 0


# --- the current fridge ---


def test_current_fridge_is_the_oldest_when_nothing_was_picked(owner, fridge):
    default_fridge = Fridge.objects.get(owner=owner, name="Мій холодильник")

    assert find_current_fridge_id(owner) == default_fridge.pk


def test_current_fridge_is_the_one_picked_last(owner, fridge):
    select_fridge(owner, fridge)

    assert find_current_fridge_id(owner) == fridge.pk
    owner.refresh_from_db()
    assert owner.last_fridge == fridge


def test_current_fridge_falls_back_when_the_user_is_no_longer_a_member(owner):
    other_owner = make_user("olga")
    shared_fridge = create_fridge(other_owner, "Спільний")
    add_member(shared_fridge, owner)
    select_fridge(owner, shared_fridge)
    FridgeMembership.objects.filter(fridge=shared_fridge, user=owner).delete()

    current_id = find_current_fridge_id(owner)

    assert current_id == Fridge.objects.get(owner=owner).pk


# --- leaving ---


def test_member_leaves_the_fridge(fridge):
    guest = make_user("olga")
    add_member(fridge, guest)

    leave_fridge(guest, fridge)

    assert not FridgeMembership.objects.filter(fridge=fridge, user=guest).exists()
    assert Fridge.objects.filter(pk=fridge.pk).exists()


def test_leaving_forgets_the_fridge_as_current(fridge):
    guest = make_user("olga")
    add_member(fridge, guest)
    select_fridge(guest, fridge)

    leave_fridge(guest, fridge)

    guest.refresh_from_db()
    assert guest.last_fridge is None


def test_leaving_keeps_another_fridge_as_current(fridge):
    guest = make_user("olga")
    add_member(fridge, guest)
    own_fridge = Fridge.objects.get(owner=guest)
    select_fridge(guest, own_fridge)

    leave_fridge(guest, fridge)

    guest.refresh_from_db()
    assert guest.last_fridge == own_fridge


def test_owner_cannot_leave(fridge, owner):
    with pytest.raises(OwnerCannotLeaveError):
        leave_fridge(owner, fridge)

    assert FridgeMembership.objects.filter(fridge=fridge, user=owner).exists()


# --- deleting ---


def test_owner_deletes_a_fridge_without_other_members(fridge):
    delete_fridge(fridge)

    assert not Fridge.objects.filter(pk=fridge.pk).exists()


def test_fridge_with_another_active_member_is_not_deleted(fridge):
    add_member(fridge, make_user("olga"))

    with pytest.raises(FridgeHasMembersError):
        delete_fridge(fridge)

    assert Fridge.objects.filter(pk=fridge.pk).exists()


def test_a_pending_request_does_not_block_deleting(fridge):
    guest = make_user("olga")
    add_member(fridge, guest, status=MembershipStatus.PENDING)

    delete_fridge(fridge)

    assert not Fridge.objects.filter(pk=fridge.pk).exists()
    assert not FridgeMembership.objects.filter(user=guest, fridge=fridge).exists()


def test_deleting_the_current_fridge_forgets_it(fridge, owner):
    select_fridge(owner, fridge)

    delete_fridge(fridge)

    owner.refresh_from_db()
    assert owner.last_fridge is None
