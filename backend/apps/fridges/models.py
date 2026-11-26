"""Fridges models: a fridge and who may use it.

A fridge has one owner and any number of members. The owner is also a
member, with the role ``owner``. A member is either ``active`` (may use
the fridge) or ``pending`` (asked to join, not approved yet). Only active
members may see a fridge; the rule lives in ``permissions.py``.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class FridgeRole(models.TextChoices):
    """What a member may do in a fridge."""

    OWNER = "owner", "Власник"
    MEMBER = "member", "Учасник"


class MembershipStatus(models.TextChoices):
    """Whether a member may already use the fridge."""

    ACTIVE = "active", "Активний"
    PENDING = "pending", "Очікує підтвердження"


class FridgeQuerySet(models.QuerySet):
    def visible_to(self, user):
        """Keep only the fridges where the user is an active member."""
        return self.filter(
            memberships__user=user,
            memberships__status=MembershipStatus.ACTIVE,
        )


class Fridge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_fridges",
    )
    created_at = models.DateTimeField(default=timezone.now)

    objects = FridgeQuerySet.as_manager()

    def __str__(self):
        return self.name


class FridgeMembership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fridge = models.ForeignKey(
        Fridge,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fridge_memberships",
    )
    role = models.CharField(
        max_length=6,
        choices=FridgeRole.choices,
        default=FridgeRole.MEMBER,
    )
    status = models.CharField(
        max_length=7,
        choices=MembershipStatus.choices,
        default=MembershipStatus.PENDING,
    )
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["fridge", "user"],
                name="fridges_membership_unique_user",
            ),
        ]

    def __str__(self):
        return f"{self.user} in {self.fridge} ({self.role}, {self.status})"
