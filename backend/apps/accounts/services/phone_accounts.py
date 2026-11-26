"""Accounts that are found and created by phone number."""

import uuid

from django.db import IntegrityError, transaction

from apps.accounts.models import User

NICKNAME_PREFIX = "user_"
NICKNAME_SUFFIX_LENGTH = 12


def get_or_create_phone_user(phone):
    """Return ``(user, is_created)`` for a normalized phone number.

    The same number always gives the same account. A new account has no
    password and a generated nickname that the person changes later. The
    number is never put into the nickname, because nicknames are shown to
    other people.
    """
    user = User.objects.filter(phone=phone).first()
    if user is not None:
        return user, False
    try:
        with transaction.atomic():
            user = User.objects.create_user(generate_nickname(), phone=phone)
    except IntegrityError:
        # Two first logins of one number can race: take the winner's row.
        user = User.objects.filter(phone=phone).first()
        if user is None:
            raise
        return user, False
    return user, True


def generate_nickname():
    """Return a unique-looking nickname that does not reveal any contact."""
    return NICKNAME_PREFIX + uuid.uuid4().hex[:NICKNAME_SUFFIX_LENGTH]
