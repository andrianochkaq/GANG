"""Fridge rules that more than one place needs."""

from django.db import transaction

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
