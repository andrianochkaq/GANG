"""DRF throttles for the endpoints that send one-time codes.

They are the first, cheap line of defence: counters live in Redis, so a
flood is stopped before it reaches the database. The service in
``services/codes.py`` enforces the same limits again for every caller.
"""

import hashlib
from collections.abc import Mapping

from rest_framework.throttling import SimpleRateThrottle

from apps.accounts.services.codes import normalize_target

# Request fields that name the target of a code.
TARGET_FIELD_NAMES = ("email", "phone", "telegram_id")


class CodeIpThrottle(SimpleRateThrottle):
    """At most 5 code requests per hour from one IP address."""

    scope = "code_ip"

    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }


class CodeTargetThrottle(SimpleRateThrottle):
    """At most 5 code requests per hour for one email, phone or Telegram id."""

    scope = "code_target"

    def get_cache_key(self, request, view):
        target = _read_target(request)
        if target is None:
            return None
        # The target is personal data, so Redis only sees its hash.
        target_hash = hashlib.sha256(normalize_target(target).encode()).hexdigest()
        return self.cache_format % {"scope": self.scope, "ident": target_hash}


class TelegramStartThrottle(SimpleRateThrottle):
    """At most 20 Telegram login requests per hour from one IP address."""

    scope = "telegram_start"

    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }


def _read_target(request):
    data = request.data
    if not isinstance(data, Mapping):
        return None
    for field_name in TARGET_FIELD_NAMES:
        value = data.get(field_name)
        if value not in (None, ""):
            return value
    return None
