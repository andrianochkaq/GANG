"""Response builders shared by the accounts views."""

from django.contrib.auth.models import update_last_login
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken


def build_error_response(code, detail, http_status, **extra):
    """Build the error body of docs/architecture.md, 5.4."""
    body = {"code": code, "detail": detail, "fields": {}, **extra}
    headers = {}
    if "retry_after_seconds" in extra:
        headers["Retry-After"] = str(extra["retry_after_seconds"])
    return Response(body, status=http_status, headers=headers)


def build_validation_error_response(serializer):
    fields = {
        field_name: [str(message) for message in messages]
        for field_name, messages in serializer.errors.items()
    }
    response = build_error_response(
        "validation_error",
        "Перевірте введені дані.",
        status.HTTP_400_BAD_REQUEST,
    )
    response.data["fields"] = fields
    return response


def build_token_response(user, is_new_user):
    """Log the user in: note the time and return a JWT pair."""
    update_last_login(None, user)
    refresh = RefreshToken.for_user(user)
    return Response(
        {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "is_new_user": is_new_user,
        }
    )
