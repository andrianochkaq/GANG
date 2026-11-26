"""Registration and login by email with a confirmation code.

``start_email_registration`` creates an account that cannot sign in yet
and returns a code to email. ``verify_email_code`` uses the code up and
verifies the email. ``authenticate_email_user`` is the password login;
it refuses accounts whose email is not verified. Every refusal is an
``EmailAuthError`` subclass that the API layer turns into a message.
"""

import re
import secrets
import uuid

from django.contrib.auth.hashers import make_password
from django.db import transaction

from apps.accounts.models import CodePurpose, User
from apps.accounts.services.codes import CodeInvalidError, issue_code, verify_code

NICKNAME_BASE_MAX_LENGTH = 20
NICKNAME_FALLBACK = "user"
NICKNAME_SUFFIX_ATTEMPTS = 10

# What UnicodeUsernameValidator allows, minus "@".
_NICKNAME_FORBIDDEN_CHARACTERS = re.compile(r"[^\w.+-]")


class EmailAuthError(Exception):
    """Base class for every refusal of an email registration or login."""


class EmailAlreadyRegisteredError(EmailAuthError):
    """The email belongs to an account that is already verified."""


class InvalidCredentialsError(EmailAuthError):
    """Unknown email, wrong password or a disabled account."""


class EmailNotVerifiedError(EmailAuthError):
    """The password is right, but the code was never entered."""


def start_email_registration(email, password, ip_address=None):
    """Create an unverified user and return the code to email to them.

    Registering again with an email that is still unverified sets the new
    password and issues a new code. When the code cannot be issued (resend
    cooldown, request limits) nothing is saved.
    """
    with transaction.atomic():
        user = User.objects.select_for_update().filter(email__iexact=email).first()
        if user is None:
            User.objects.create_user(
                _build_unique_nickname(email),
                password=password,
                email=email,
            )
        elif user.is_email_verified:
            raise EmailAlreadyRegisteredError()
        else:
            user.set_password(password)
            user.save(update_fields=["password"])
        return issue_code(CodePurpose.EMAIL_VERIFICATION, email, ip_address)


def resend_email_code(email, ip_address=None):
    """Return a new code for an unverified account, or None if there is none.

    The caller answers the same way in both cases, so the endpoint does not
    tell whether an email is registered.
    """
    is_waiting = User.objects.filter(
        email__iexact=email,
        is_active=True,
        is_email_verified=False,
    ).exists()
    if not is_waiting:
        return None
    return issue_code(CodePurpose.EMAIL_VERIFICATION, email, ip_address)


def verify_email_code(email, code):
    """Use the code up, mark the email as verified and return the user."""
    verify_code(CodePurpose.EMAIL_VERIFICATION, email, code)
    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user is None:
        raise CodeInvalidError()
    if not user.is_email_verified:
        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])
    return user


def authenticate_email_user(email, password):
    """Return the user for a right email and password, or raise."""
    user = User.objects.filter(email__iexact=email).first()
    if user is None:
        # Hash anyway, so an unknown email does not answer faster.
        make_password(password)
        raise InvalidCredentialsError()
    if not user.is_active or not user.check_password(password):
        raise InvalidCredentialsError()
    if not user.is_email_verified:
        raise EmailNotVerifiedError()
    return user


def _build_unique_nickname(email):
    # The nickname is required and unique but registration does not ask
    # for one, so it starts as the part of the email before the "@".
    local_part = User.normalize_username(email.split("@")[0])
    base = _NICKNAME_FORBIDDEN_CHARACTERS.sub("", local_part)
    base = base[:NICKNAME_BASE_MAX_LENGTH] or NICKNAME_FALLBACK
    if not _is_nickname_taken(base):
        return base
    for _ in range(NICKNAME_SUFFIX_ATTEMPTS):
        candidate = f"{base}{secrets.randbelow(10000):04d}"
        if not _is_nickname_taken(candidate):
            return candidate
    return f"{base[:10]}{uuid.uuid4().hex[:12]}"


def _is_nickname_taken(nickname):
    return User.objects.filter(nickname__iexact=nickname).exists()
