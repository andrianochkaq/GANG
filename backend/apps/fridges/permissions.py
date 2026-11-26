"""One access rule for every fridge endpoint.

Only active members may see a fridge. Everybody else, including people
whose request to join is still pending, gets 404 and not 403, so fridge
ids cannot be probed.

Use ``IsFridgeMember`` on a view in one of two ways:

* the URL has a ``fridge_id`` (``/api/fridges/<fridge_id>/...``): the
  check runs before the view does anything;
* the view loads an object with ``get_object()``: the object is a
  ``Fridge`` or has a ``fridge`` field, and the check runs on it.
"""

from django.core.exceptions import ValidationError
from django.http import Http404
from rest_framework.permissions import BasePermission

from .models import Fridge, FridgeMembership, MembershipStatus


def _is_active_member(user, fridge_id):
    try:
        return FridgeMembership.objects.filter(
            fridge_id=fridge_id,
            user=user,
            status=MembershipStatus.ACTIVE,
        ).exists()
    except (ValueError, ValidationError):
        # Not a valid fridge id, so no such fridge.
        return False


class IsFridgeMember(BasePermission):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        fridge_id = view.kwargs.get("fridge_id")
        if fridge_id is not None and not _is_active_member(request.user, fridge_id):
            raise Http404
        return True

    def has_object_permission(self, request, view, obj):
        fridge = obj if isinstance(obj, Fridge) else getattr(obj, "fridge", None)
        if fridge is None or not _is_active_member(request.user, fridge.pk):
            raise Http404
        return True
