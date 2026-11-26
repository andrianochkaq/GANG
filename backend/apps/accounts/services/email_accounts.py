"""Accounts that are found and created by email and password."""

from django.contrib.auth.hashers import make_password
from django.db import IntegrityError, transaction

from apps.accounts.models import User
from apps.accounts.services.phone_accounts import generate_nickname


def find_user_by_email(email):
    """Return the user with this email, ignoring letter case, or ``None``."""
    return User.objects.filter(email__iexact=email).first()


def register_email_user(email, password):
    """Create an account that waits for its code; return it, or ``None``.

    An email that is already confirmed keeps its account and its password,
    and ``None`` is returned. An email that was never confirmed gets the new
    password: only the owner of the mailbox can finish the sign-up anyway.
    """
    user = find_user_by_email(email)
    if user is None:
        try:
            with transaction.atomic():
                return User.objects.create_user(
                    generate_nickname(),
                    password=password,
                    email=email,
                )
        except IntegrityError:
            # Two sign-ups with one email can race: take the winner's row.
            user = find_user_by_email(email)
            if user is None:
                raise
    if user.is_email_verified:
        return None
    user.set_password(password)
    user.save(update_fields=["password"])
    return user


def confirm_email(user):
    """Mark the email of the user as confirmed."""
    user.is_email_verified = True
    user.save(update_fields=["is_email_verified"])


def burn_password_check_time(password):
    """Hash a password for nothing, so an unknown email answers as slowly."""
    make_password(password)
