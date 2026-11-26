"""Login through the Telegram bot: start, poll the status, receive updates.

There is no password anywhere in this flow. A Telegram id that has no
account yet gets one when its login is collected.
"""

from django.conf import settings
from django.utils.crypto import constant_time_compare
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.serializers import (
    ApiErrorSerializer,
    TelegramLoginStartedSerializer,
    TelegramLoginStatusSerializer,
)
from apps.accounts.services.telegram_login import (
    LOGIN_TTL_MINUTES,
    TelegramLoginExpiredError,
    TelegramLoginNotFoundError,
    read_login_result,
    start_login_request,
)
from apps.accounts.telegram_bot import handle_update
from apps.accounts.throttles import TelegramStartThrottle
from apps.accounts.views.responses import build_error_response, build_token_response

POLL_INTERVAL_SECONDS = 2
WEBHOOK_SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"


class TelegramLoginStartView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [TelegramStartThrottle]

    @extend_schema(
        request=None,
        responses={
            200: TelegramLoginStartedSerializer,
            429: ApiErrorSerializer,
            503: ApiErrorSerializer,
        },
        summary="Start a login through the Telegram bot",
    )
    def post(self, request):
        bot_username = settings.TELEGRAM_BOT_USERNAME
        if not bot_username:
            return build_error_response(
                "telegram_unavailable",
                "Вхід через Telegram тимчасово недоступний.",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        login_request = start_login_request()
        return Response(
            {
                "token": login_request.token,
                "deep_link": f"https://t.me/{bot_username}?start={login_request.token}",
                "expires_in_seconds": LOGIN_TTL_MINUTES * 60,
                "poll_interval_seconds": POLL_INTERVAL_SECONDS,
            }
        )


class TelegramLoginStatusView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        responses={
            200: TelegramLoginStatusSerializer,
            403: ApiErrorSerializer,
            404: ApiErrorSerializer,
            410: ApiErrorSerializer,
        },
        summary="Poll a Telegram login; the JWT pair is given out once",
    )
    def get(self, request, token):
        try:
            result = read_login_result(token)
        except TelegramLoginNotFoundError:
            return build_error_response(
                "telegram_login_not_found",
                "Запит на вхід не знайдено. Спробуйте ще раз.",
                status.HTTP_404_NOT_FOUND,
            )
        except TelegramLoginExpiredError:
            return build_error_response(
                "telegram_login_expired",
                f"Вхід діє {LOGIN_TTL_MINUTES} хв і вже не дійсний. Спробуйте ще раз.",
                status.HTTP_410_GONE,
            )
        if result is None:
            return Response({"status": "pending"})
        user, is_new_user = result
        if not user.is_active:
            return build_error_response(
                "account_disabled",
                "Обліковий запис вимкнено.",
                status.HTTP_403_FORBIDDEN,
            )
        token_response = build_token_response(user, is_new_user)
        token_response.data["status"] = "confirmed"
        return token_response


class TelegramWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(exclude=True)
    def post(self, request):
        if not _is_webhook_secret_valid(request):
            return build_error_response(
                "webhook_forbidden",
                "Доступ заборонено.",
                status.HTTP_403_FORBIDDEN,
            )
        handle_update(request.data)
        # Telegram repeats the call until it gets a 200.
        return Response({})


def _is_webhook_secret_valid(request):
    secret = settings.TELEGRAM_WEBHOOK_SECRET
    if not secret:
        return False
    return constant_time_compare(request.headers.get(WEBHOOK_SECRET_HEADER, ""), secret)
