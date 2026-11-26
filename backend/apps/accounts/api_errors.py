"""Error responses of the account API.

Every error body has the shape from docs/architecture.md:
``{"code": "...", "detail": "Ukrainian message", "fields": {...}}``.
``handle_api_exception`` turns validation errors, throttling and the
refusals of the code and email services into that shape. Anything else
goes to the default DRF handler.
"""

import math

from rest_framework import status
from rest_framework.exceptions import Throttled, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from apps.accounts.services.codes import (
    CodeAttemptsExceededError,
    CodeExpiredError,
    CodeInvalidError,
    CodeRequestLimitError,
    CodeResendTooSoonError,
)
from apps.accounts.services.email_auth import (
    EmailAlreadyRegisteredError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
)

VALIDATION_ERROR_DETAIL = "Перевірте введені дані."
THROTTLED_DETAIL = "Забагато запитів. Спробуйте ще раз через {seconds} с."

# (exception, code, detail, HTTP status). "{seconds}" is filled in for the
# errors that carry ``retry_after_seconds``.
_ERROR_RULES = (
    (
        CodeResendTooSoonError,
        "code_resend_too_soon",
        "Новий код можна запросити через {seconds} с.",
        status.HTTP_429_TOO_MANY_REQUESTS,
    ),
    (
        CodeRequestLimitError,
        "code_request_limit",
        "Забагато кодів за годину. Спробуйте ще раз через {seconds} с.",
        status.HTTP_429_TOO_MANY_REQUESTS,
    ),
    (
        CodeExpiredError,
        "code_expired",
        "Код застарів. Запросіть новий.",
        status.HTTP_400_BAD_REQUEST,
    ),
    (
        CodeAttemptsExceededError,
        "code_attempts_exceeded",
        "Забагато невдалих спроб. Запросіть новий код.",
        status.HTTP_400_BAD_REQUEST,
    ),
    (
        CodeInvalidError,
        "code_invalid",
        "Код не підходить. Перевірте його і спробуйте ще раз.",
        status.HTTP_400_BAD_REQUEST,
    ),
    (
        EmailAlreadyRegisteredError,
        "email_taken",
        "Цей email уже зареєстровано. Увійдіть або вкажіть інший.",
        status.HTTP_409_CONFLICT,
    ),
    (
        EmailNotVerifiedError,
        "email_not_verified",
        "Email ще не підтверджено. Введіть код із листа або запросіть новий.",
        status.HTTP_403_FORBIDDEN,
    ),
    (
        InvalidCredentialsError,
        "invalid_credentials",
        "Невірний email або пароль.",
        status.HTTP_401_UNAUTHORIZED,
    ),
)


def build_error_response(code, detail, http_status, fields=None, extra=None):
    body = {"code": code, "detail": detail, "fields": fields or {}}
    body.update(extra or {})
    return Response(body, status=http_status)


def handle_api_exception(exc, context):
    if isinstance(exc, ValidationError):
        return build_error_response(
            "validation_error",
            VALIDATION_ERROR_DETAIL,
            status.HTTP_400_BAD_REQUEST,
            fields=_flatten_field_errors(exc.detail),
        )
    if isinstance(exc, Throttled):
        seconds = math.ceil(exc.wait) if exc.wait else 1
        return _build_retry_response(
            "too_many_requests",
            THROTTLED_DETAIL.format(seconds=seconds),
            status.HTTP_429_TOO_MANY_REQUESTS,
            seconds,
        )
    for error_class, code, detail, http_status in _ERROR_RULES:
        if isinstance(exc, error_class):
            return _build_rule_response(exc, code, detail, http_status)
    return exception_handler(exc, context)


def _build_rule_response(exc, code, detail, http_status):
    retry_after_seconds = getattr(exc, "retry_after_seconds", None)
    attempts_left = getattr(exc, "attempts_left", None)
    detail = detail.format(seconds=retry_after_seconds)
    if retry_after_seconds is not None:
        return _build_retry_response(code, detail, http_status, retry_after_seconds)
    extra = {}
    if attempts_left is not None:
        extra["attempts_left"] = attempts_left
    return build_error_response(code, detail, http_status, extra=extra)


def _build_retry_response(code, detail, http_status, retry_after_seconds):
    response = build_error_response(
        code,
        detail,
        http_status,
        extra={"retry_after_seconds": retry_after_seconds},
    )
    response["Retry-After"] = str(retry_after_seconds)
    return response


def _flatten_field_errors(detail):
    if not isinstance(detail, dict):
        return {"non_field_errors": _as_messages(detail)}
    fields = {}
    for field_name, messages in detail.items():
        fields[str(field_name)] = _as_messages(messages)
    return fields


def _as_messages(messages):
    if isinstance(messages, list | tuple):
        return [str(message) for message in messages]
    return [str(messages)]
