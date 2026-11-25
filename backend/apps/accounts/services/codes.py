"""One-time codes for email verification, phone login and Telegram login.

``issue_code`` creates a 6-digit code and returns it so the caller can send
it. The database keeps only a keyed hash. ``verify_code`` checks what the
person typed. Every refusal is a ``CodeError`` subclass that the API layer
turns into a Ukrainian message.

Rules:
- a code is valid for 10 minutes and for 5 wrong attempts;
- a new code can be requested 60 seconds after the previous one, and it
  replaces the previous one;
- at most 5 codes per hour for one target and for one IP address.
"""

import math
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac

from apps.accounts.models import CodePurpose, OneTimeCode

CODE_LENGTH = 6
CODE_TTL_MINUTES = 10
MAX_CODE_ATTEMPTS = 5
RESEND_COOLDOWN_SECONDS = 60
MAX_CODE_REQUESTS_PER_HOUR = 5
REQUEST_WINDOW_MINUTES = 60

_HASH_KEY_SALT = "apps.accounts.services.codes"


class CodeError(Exception):
    """Base class for every refusal of a code request or check."""


class CodeResendTooSoonError(CodeError):
    """A new code was asked for before the resend cooldown ended."""

    def __init__(self, retry_after_seconds):
        super().__init__(f"Retry in {retry_after_seconds} seconds.")
        self.retry_after_seconds = retry_after_seconds


class CodeRequestLimitError(CodeError):
    """Too many codes were requested for one target or from one IP address."""

    def __init__(self, retry_after_seconds):
        super().__init__(f"Retry in {retry_after_seconds} seconds.")
        self.retry_after_seconds = retry_after_seconds


class CodeExpiredError(CodeError):
    """The code is older than ``CODE_TTL_MINUTES``."""


class CodeAttemptsExceededError(CodeError):
    """The code was typed wrongly ``MAX_CODE_ATTEMPTS`` times."""


class CodeInvalidError(CodeError):
    """No such code, or the code is wrong."""

    def __init__(self, attempts_left=0):
        super().__init__("The code is not valid.")
        self.attempts_left = attempts_left


def normalize_target(target):
    """Return the form of an email, phone or Telegram id that codes use."""
    return str(target).strip().lower()


def issue_code(purpose, target, ip_address=None):
    """Create a code for the target and return it in plain text.

    The plain code exists only in the return value: send it and forget it.
    Older unused codes for the same purpose and target stop working.
    """
    purpose = CodePurpose(purpose).value
    target = normalize_target(target)
    now = _get_current_time()
    with transaction.atomic():
        _lock_target(target)
        _check_request_limits(target, ip_address, now)
        _check_resend_cooldown(purpose, target, now)
        OneTimeCode.objects.filter(
            purpose=purpose,
            target=target,
            is_used=False,
        ).update(is_used=True)
        code = _generate_code()
        OneTimeCode.objects.create(
            purpose=purpose,
            target=target,
            code_hash=_hash_code(purpose, target, code),
            ip_address=ip_address,
            created_at=now,
            expires_at=now + timedelta(minutes=CODE_TTL_MINUTES),
        )
    return code


def verify_code(purpose, target, code):
    """Accept the code once, or raise a ``CodeError``.

    A correct code is used up. A wrong one costs an attempt, and after
    ``MAX_CODE_ATTEMPTS`` of them even the correct code is refused.
    """
    purpose = CodePurpose(purpose).value
    target = normalize_target(target)
    now = _get_current_time()
    error = None
    # Raising inside the block would roll the attempt counter back, so the
    # error is raised after the transaction has been committed.
    with transaction.atomic():
        one_time_code = (
            OneTimeCode.objects.select_for_update()
            .filter(purpose=purpose, target=target, is_used=False)
            .order_by("-created_at")
            .first()
        )
        if one_time_code is None:
            error = CodeInvalidError()
        elif one_time_code.expires_at <= now:
            error = CodeExpiredError()
        elif one_time_code.attempt_count >= MAX_CODE_ATTEMPTS:
            error = CodeAttemptsExceededError()
        elif not constant_time_compare(
            one_time_code.code_hash,
            _hash_code(purpose, target, str(code).strip()),
        ):
            one_time_code.attempt_count += 1
            one_time_code.save(update_fields=["attempt_count"])
            error = CodeInvalidError(MAX_CODE_ATTEMPTS - one_time_code.attempt_count)
        else:
            one_time_code.is_used = True
            one_time_code.save(update_fields=["is_used"])
    if error is not None:
        raise error


def delete_expired_codes():
    """Delete codes the hourly limits no longer count; return how many.

    Every code is expired long before it leaves the request window, so
    nothing that could still be accepted is removed.
    """
    window_start = _get_current_time() - timedelta(minutes=REQUEST_WINDOW_MINUTES)
    deleted_count, _ = OneTimeCode.objects.filter(created_at__lte=window_start).delete()
    return deleted_count


def _get_current_time():
    return timezone.now()


def _generate_code():
    return f"{secrets.randbelow(10**CODE_LENGTH):0{CODE_LENGTH}d}"


def _hash_code(purpose, target, code):
    # A keyed hash: six digits alone could be reversed from a leaked table.
    return salted_hmac(
        _HASH_KEY_SALT,
        f"{purpose}:{target}:{code}",
        secret=settings.SECRET_KEY,
        algorithm="sha256",
    ).hexdigest()


def _lock_target(target):
    # Two simultaneous requests must not both pass the limit checks. The
    # lock is released when the surrounding transaction ends.
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", [target])


def _check_request_limits(target, ip_address, now):
    window_start = now - timedelta(minutes=REQUEST_WINDOW_MINUTES)
    recent_codes = OneTimeCode.objects.filter(created_at__gt=window_start)
    scopes = [recent_codes.filter(target=target)]
    if ip_address:
        scopes.append(recent_codes.filter(ip_address=ip_address))
    for scope in scopes:
        if scope.count() >= MAX_CODE_REQUESTS_PER_HOUR:
            oldest_created_at = scope.order_by("created_at").first().created_at
            free_at = oldest_created_at + timedelta(minutes=REQUEST_WINDOW_MINUTES)
            raise CodeRequestLimitError(_count_seconds_until(free_at, now))


def _check_resend_cooldown(purpose, target, now):
    latest_code = (
        OneTimeCode.objects.filter(purpose=purpose, target=target)
        .order_by("-created_at")
        .first()
    )
    if latest_code is None:
        return
    free_at = latest_code.created_at + timedelta(seconds=RESEND_COOLDOWN_SECONDS)
    if free_at > now:
        raise CodeResendTooSoonError(_count_seconds_until(free_at, now))


def _count_seconds_until(moment, now):
    return max(1, math.ceil((moment - now).total_seconds()))
