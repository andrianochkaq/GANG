"""Login by phone: ask for an SMS code, then trade it for a JWT pair.

There is no password anywhere in this flow. A number that has no account
yet gets one when its first code is accepted.
"""

import ipaddress
import math

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import CodePurpose
from apps.accounts.serializers import (
    ApiErrorSerializer,
    PhoneCodeRequestSerializer,
    PhoneCodeSentSerializer,
    PhoneLoginResultSerializer,
    PhoneLoginSerializer,
)
from apps.accounts.services.codes import (
    CODE_TTL_MINUTES,
    RESEND_COOLDOWN_SECONDS,
    CodeAttemptsExceededError,
    CodeExpiredError,
    CodeInvalidError,
    CodeRequestLimitError,
    CodeResendTooSoonError,
    issue_code,
    verify_code,
)
from apps.accounts.services.phone_accounts import get_or_create_phone_user
from apps.accounts.throttles import CodeIpThrottle, CodeTargetThrottle
from apps.accounts.views.responses import (
    build_error_response,
    build_token_response,
    build_validation_error_response,
)
from core.sms import SmsError, send_sms


class PhoneCodeRequestView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [CodeIpThrottle, CodeTargetThrottle]

    @extend_schema(
        request=PhoneCodeRequestSerializer,
        responses={
            200: PhoneCodeSentSerializer,
            400: ApiErrorSerializer,
            429: ApiErrorSerializer,
            503: ApiErrorSerializer,
        },
        summary="Send a login code by SMS",
    )
    def post(self, request):
        serializer = PhoneCodeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return build_validation_error_response(serializer)
        phone = serializer.validated_data["phone"]
        try:
            code = issue_code(
                CodePurpose.PHONE_LOGIN,
                phone,
                ip_address=_read_client_ip(request),
            )
        except CodeResendTooSoonError as error:
            return build_error_response(
                "code_resend_too_soon",
                f"Новий код можна запросити через {error.retry_after_seconds} с.",
                status.HTTP_429_TOO_MANY_REQUESTS,
                retry_after_seconds=error.retry_after_seconds,
            )
        except CodeRequestLimitError as error:
            minutes = math.ceil(error.retry_after_seconds / 60)
            return build_error_response(
                "code_request_limit",
                f"Забагато запитів коду. Спробуйте через {minutes} хв.",
                status.HTTP_429_TOO_MANY_REQUESTS,
                retry_after_seconds=error.retry_after_seconds,
            )
        try:
            send_sms(phone, _build_code_text(code))
        except SmsError:
            return build_error_response(
                "sms_unavailable",
                "Не вдалося надіслати SMS. Спробуйте трохи пізніше.",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        # The answer is the same for a known and a new number, so it does
        # not reveal who has an account.
        return Response({"resend_after_seconds": RESEND_COOLDOWN_SECONDS})


class PhoneLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        request=PhoneLoginSerializer,
        responses={
            200: PhoneLoginResultSerializer,
            400: ApiErrorSerializer,
            403: ApiErrorSerializer,
        },
        summary="Log in, or sign up, with a phone number and an SMS code",
    )
    def post(self, request):
        serializer = PhoneLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return build_validation_error_response(serializer)
        phone = serializer.validated_data["phone"]
        code = serializer.validated_data["code"]
        try:
            verify_code(CodePurpose.PHONE_LOGIN, phone, code)
        except CodeInvalidError as error:
            return build_error_response(
                "code_invalid",
                f"Код не підходить. Залишилось спроб: {error.attempts_left}.",
                status.HTTP_400_BAD_REQUEST,
                attempts_left=error.attempts_left,
            )
        except CodeExpiredError:
            return build_error_response(
                "code_expired",
                f"Код діє {CODE_TTL_MINUTES} хв і вже не дійсний. Запросіть новий.",
                status.HTTP_400_BAD_REQUEST,
            )
        except CodeAttemptsExceededError:
            return build_error_response(
                "code_attempts_exceeded",
                "Забагато хибних спроб. Запросіть новий код.",
                status.HTTP_400_BAD_REQUEST,
            )
        user, is_new_user = get_or_create_phone_user(phone)
        if not user.is_active:
            return build_error_response(
                "account_disabled",
                "Обліковий запис вимкнено.",
                status.HTTP_403_FORBIDDEN,
            )
        return build_token_response(user, is_new_user)


def _build_code_text(code):
    return f"FreeCook: код входу {code}. Діє {CODE_TTL_MINUTES} хв."


def _read_client_ip(request):
    # The same address the throttles use, so both limits see one client.
    identity = CodeIpThrottle().get_ident(request)
    try:
        return str(ipaddress.ip_address(identity))
    except ValueError:
        return None
