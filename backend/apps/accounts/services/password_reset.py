"""Password reset by an email link.

The link carries the user id and a Django reset token. The token is a hash
of the user's password, last login and email plus a timestamp, so it stops
working when the password changes (it works once) and after
``PASSWORD_RESET_TIMEOUT`` (one hour). Nothing about it is stored.

Only an email account with a confirmed email and a password can reset it.
Phone and Telegram accounts have no password to reset.
"""

from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from apps.accounts.models import User
from apps.accounts.services.email_accounts import find_user_by_email

# The page of the React app that the link opens (frontend/src/routes).
RESET_PAGE_PATH = "/reset-password"


def find_user_for_password_reset(email):
    """Return the user who may reset the password of this email, or ``None``."""
    user = find_user_by_email(email)
    if user is None or not _can_reset_password(user):
        return None
    return user


def build_reset_url(user):
    """Return the link to the reset page with the user id and a fresh token."""
    query = urlencode(
        {
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": default_token_generator.make_token(user),
        }
    )
    return f"{settings.FRONTEND_URL.rstrip('/')}{RESET_PAGE_PATH}?{query}"


def find_user_by_reset_link(uid, token):
    """Return the user a valid, unused, unexpired link belongs to, or ``None``."""
    try:
        user = User.objects.get(pk=force_str(urlsafe_base64_decode(uid)))
    except (
        TypeError,
        ValueError,
        OverflowError,
        DjangoValidationError,
        User.DoesNotExist,
    ):
        return None
    if not _can_reset_password(user):
        return None
    if not default_token_generator.check_token(user, token):
        return None
    return user


def set_new_password(user, password):
    """Save the new password and end every session of the user.

    Changing the password also makes the link that was used invalid.
    """
    with transaction.atomic():
        user.set_password(password)
        user.save(update_fields=["password"])
        revoke_user_sessions(user)


def revoke_user_sessions(user):
    """Revoke every refresh token of the user, so no device stays logged in."""
    for outstanding_token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=outstanding_token)


def _can_reset_password(user):
    return (
        user.is_active
        and user.email is not None
        and user.is_email_verified
        and user.has_usable_password()
    )
