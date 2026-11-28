"""Fridge rules that more than one place needs."""

from django.db import transaction
from django.db.models import Count, IntegerField, OuterRef, Subquery
from django.db.models.functions import Coalesce

from apps.products.models import FridgeItem

from .models import Fridge, FridgeMembership, FridgeRole, MembershipStatus

DEFAULT_FRIDGE_NAME = "Мій холодильник"


@transaction.atomic
def create_fridge(owner, name):
    """Create a fridge and make its owner an active member with role owner."""
    fridge = Fridge.objects.create(name=name, owner=owner)
    FridgeMembership.objects.create(
        fridge=fridge,
        user=owner,
        role=FridgeRole.OWNER,
        status=MembershipStatus.ACTIVE,
    )
    return fridge


@transaction.atomic
def create_default_fridge(user):
    """Give the user their first fridge; do nothing if they already own one."""
    existing_fridge = Fridge.objects.filter(owner=user).first()
    if existing_fridge is not None:
        return existing_fridge
    return create_fridge(user, DEFAULT_FRIDGE_NAME)


class FridgeHasMembersError(Exception):
    """The fridge cannot be deleted: other people still use it."""


class OwnerCannotLeaveError(Exception):
    """The owner cannot leave. Handing the fridge over is FC-708."""


def annotate_fridge_summary(fridges):
    """Add ``member_count`` and ``product_count`` to a queryset of fridges.

    The members and the items are counted in subqueries, because a filter on
    the same relation (``visible_to``) would otherwise leave only the
    caller's row.
    """
    active_members = (
        FridgeMembership.objects.filter(
            fridge=OuterRef("pk"),
            status=MembershipStatus.ACTIVE,
        )
        .order_by()
        .values("fridge")
        .annotate(total=Count("pk"))
        .values("total")
    )
    items = (
        FridgeItem.objects.filter(fridge=OuterRef("pk"))
        .order_by()
        .values("fridge")
        .annotate(total=Count("pk"))
        .values("total")
    )
    return fridges.annotate(
        member_count=Coalesce(
            Subquery(active_members),
            0,
            output_field=IntegerField(),
        ),
        product_count=Coalesce(
            Subquery(items),
            0,
            output_field=IntegerField(),
        ),
    )


def find_current_fridge_id(user):
    """Return the id of the fridge the user is working in, or ``None``.

    It is the fridge picked last if the user is still a member of it;
    otherwise the oldest fridge of the user.
    """
    visible_fridges = Fridge.objects.visible_to(user)
    if user.last_fridge_id is not None:
        if visible_fridges.filter(pk=user.last_fridge_id).exists():
            return user.last_fridge_id
    return (
        visible_fridges.order_by("created_at", "pk")
        .values_list("pk", flat=True)
        .first()
    )


def select_fridge(user, fridge):
    """Remember the fridge as the one the user works in."""
    user.last_fridge = fridge
    user.save(update_fields=["last_fridge"])


@transaction.atomic
def leave_fridge(user, fridge):
    """Remove the user from the fridge; the owner cannot leave it."""
    if fridge.owner_id == user.pk:
        raise OwnerCannotLeaveError
    FridgeMembership.objects.filter(fridge=fridge, user=user).delete()
    if user.last_fridge_id == fridge.pk:
        user.last_fridge = None
        user.save(update_fields=["last_fridge"])


@transaction.atomic
def delete_fridge(fridge):
    """Delete a fridge that has no members besides its owner."""
    # The lock keeps a member from being approved while the fridge is checked.
    locked_fridge = Fridge.objects.select_for_update().get(pk=fridge.pk)
    other_members = FridgeMembership.objects.filter(
        fridge=locked_fridge,
        status=MembershipStatus.ACTIVE,
    ).exclude(user=locked_fridge.owner)
    if other_members.exists():
        raise FridgeHasMembersError
    locked_fridge.delete()
