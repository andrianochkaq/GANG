"""Use First: what in the fridge should be eaten before the rest.

The order is: expired items, then items that expire within three days,
then opened items, then everything else by the day it was added (oldest
first). Inside the first two groups the earliest expiry date comes first,
so an item that expires tomorrow stands above one that expires in three
days.
"""

from datetime import timedelta

from django.db.models import Case, DateField, F, IntegerField, Q, Value, When
from django.utils import timezone

USE_FIRST_SOON_DAYS = 3
USE_FIRST_LIMIT = 50

_TIER_EXPIRED = 0
_TIER_EXPIRING_SOON = 1
_TIER_OPENED = 2
_TIER_OTHER = 3


def list_use_first_items(items, today=None, limit=USE_FIRST_LIMIT):
    """Return the most urgent items of a fridge queryset, most urgent first.

    ``today`` defaults to the current date in the project time zone.
    """
    today = timezone.localdate() if today is None else today
    soon_date = today + timedelta(days=USE_FIRST_SOON_DAYS)
    tier = Case(
        When(expires_at__lt=today, then=Value(_TIER_EXPIRED)),
        When(expires_at__lte=soon_date, then=Value(_TIER_EXPIRING_SOON)),
        When(Q(opened_at__isnull=False), then=Value(_TIER_OPENED)),
        default=Value(_TIER_OTHER),
        output_field=IntegerField(),
    )
    # Only the first two groups are ordered by expiry; the rest by age.
    expiry_if_urgent = Case(
        When(expires_at__lte=soon_date, then=F("expires_at")),
        default=None,
        output_field=DateField(),
    )
    ordered = items.annotate(
        use_first_tier=tier,
        use_first_expiry=expiry_if_urgent,
    ).order_by(
        "use_first_tier",
        "use_first_expiry",
        "created_at",
        "id",
    )
    return list(ordered[:limit])
