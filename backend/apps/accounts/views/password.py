"""Forgot password: email a one-hour link, then set a new password with it.

The answer to "forgot password" is the same for every email, so it does
not reveal who has an account. A request for an unknown email, or for a
phone or Telegram account, sends nothing.
"""

import logging

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema
from kombu.exceptions import OperationalError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.serializers import (
    ApiErrorSerializer,
    PasswordForgotSerializer,
    PasswordMessageSerializer,
    PasswordResetSerializer,
)
from apps.accounts.services.password_reset import (
    build_reset_url,
    find_user_by_reset_link,
    find_user_for_password_reset,
    set_new_password,
)
from apps.accounts.tasks import send_password_reset_email
from apps.accounts.throttles import CodeIpThrottle, CodeTargetThrottle
from apps.accounts.views.responses import (
    build_error_response,
    build_validation_error_response,
)

logger = logging.getLogger(__name__)

FORGOT_MESSAGE = "Якщо такий email є у FreeCook, ми надіслали на нього лист."
RESET_DONE_MESSAGE = "Пароль змінено. Увійдіть із новим паролем."


class PasswordForgotView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [CodeIpThrottle, CodeTargetThrottle]

    @extend_schema(
        request=PasswordForgotSerializer,
        responses={
            200: PasswordMessageSerializer,
            400: ApiErrorSerializer,
            429: ApiErrorSerializer,
        },
        summary="Email a one-hour link to reset the password",
    )
    def post(self, request):
        serializer = PasswordForgotSerializer(data=request.data)
        if not serializer.is_valid():
            return build_validation_error_response(serializer)
        user = find_user_for_password_reset(serializer.validated_data["email"])
        if user is not None:
            _queue_reset_email(user)
        return Response({"detail": FORGOT_MESSAGE})


class PasswordResetView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        request=PasswordResetSerializer,
        responses={
            200: PasswordMessageSerializer,
            400: ApiErrorSerializer,
        },
        summary="Set a new password with the link from the email",
    )
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return build_validation_error_response(serializer)
        data = serializer.validated_data
        user = find_user_by_reset_link(data["uid"], data["token"])
        if user is None:
            return build_error_response(
                "reset_link_invalid",
                "Посилання не діє: його вже використано або воно застаріло. "
                "Запросіть нове.",
                status.HTTP_400_BAD_REQUEST,
            )
        try:
            validate_password(data["password"], user=user)
        except DjangoValidationError as error:
            # The link is not used up, so the person can try another password.
            response = build_error_response(
                "validation_error",
                "Перевірте введені дані.",
                status.HTTP_400_BAD_REQUEST,
            )
            response.data["fields"] = {"password": list(error.messages)}
            return response
        set_new_password(user, data["password"])
        return Response({"detail": RESET_DONE_MESSAGE})


def _queue_reset_email(user):
    """Hand the letter to Celery. A broker that is down is only logged.

    An error here would tell the caller that the email has an account, so
    the answer stays the same; the person can ask for a new link.
    """
    try:
        send_password_reset_email.delay(user.email, build_reset_url(user))
    except OperationalError:
        logger.exception("Could not queue a password reset email.")
