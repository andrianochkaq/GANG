"""Register and log in by email: a password and a code from a letter.

Signing up sends a 6-digit code. Entering the code confirms the email and
returns a JWT pair. Until then the password does not log anyone in. The
answers of the sign-up and of the code request are the same for a known
and a new email, so they do not reveal who has an account.
"""

import ipaddress
import math

from drf_spectacular.utils import extend_schema
from kombu.exceptions import OperationalError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import CodePurpose
from apps.accounts.serializers import (
    ApiErrorSerializer,
    EmailCodeRequestSerializer,
    EmailCodeSentSerializer,
    EmailLoginResultSerializer,
    EmailLoginSerializer,
    EmailRegisterSerializer,
    EmailVerifySerializer,
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
from apps.accounts.services.email_accounts import (
    burn_password_check_time,
    confirm_email,
    find_user_by_email,
    register_email_user,
)
from apps.accounts.tasks import send_email_code
from apps.accounts.throttles import CodeIpThrottle, CodeTargetThrottle
from apps.accounts.views.responses import (
    build_error_response,
    build_token_response,
    build_validation_error_response,
)


class EmailRegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [CodeIpThrottle, CodeTargetThrottle]

    @extend_schema(
        request=EmailRegisterSerializer,
        responses={
            200: EmailCodeSentSerializer,
            400: ApiErrorSerializer,
            429: ApiErrorSerializer,
            503: ApiErrorSerializer,
        },
        summary="Sign up with an email and a password, and send a code",
    )
    def post(self, request):
        serializer = EmailRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return build_validation_error_response(serializer)
        email = serializer.validated_data["email"]
        try:
            code = _issue_email_code(request, email)
        except (CodeResendTooSoonError, CodeRequestLimitError) as error:
            return _build_issue_error_response(error)
        user = register_email_user(email, serializer.validated_data["password"])
        if user is not None:
            error_response = _queue_email_code(email, code)
            if error_response is not None:
                return error_response
        return Response({"resend_after_seconds": RESEND_COOLDOWN_SECONDS})


class EmailCodeRequestView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [CodeIpThrottle, CodeTargetThrottle]

    @extend_schema(
        request=EmailCodeRequestSerializer,
        responses={
            200: EmailCodeSentSerializer,
            400: ApiErrorSerializer,
            429: ApiErrorSerializer,
            503: ApiErrorSerializer,
        },
        summary="Send a new confirmation code to an email that is not confirmed",
    )
    def post(self, request):
        serializer = EmailCodeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return build_validation_error_response(serializer)
        email = serializer.validated_data["email"]
        try:
            code = _issue_email_code(request, email)
        except (CodeResendTooSoonError, CodeRequestLimitError) as error:
            return _build_issue_error_response(error)
        user = find_user_by_email(email)
        if user is not None and not user.is_email_verified:
            error_response = _queue_email_code(email, code)
            if error_response is not None:
                return error_response
        return Response({"resend_after_seconds": RESEND_COOLDOWN_SECONDS})


class EmailVerifyView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        request=EmailVerifySerializer,
        responses={
            200: EmailLoginResultSerializer,
            400: ApiErrorSerializer,
            403: ApiErrorSerializer,
        },
        summary="Confirm the email with the code and receive a JWT pair",
    )
    def post(self, request):
        serializer = EmailVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return build_validation_error_response(serializer)
        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]
        try:
            verify_code(CodePurpose.EMAIL_VERIFICATION, email, code)
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
        user = find_user_by_email(email)
        if user is None:
            return build_error_response(
                "code_invalid",
                "Код не підходить. Запросіть новий.",
                status.HTTP_400_BAD_REQUEST,
            )
        if not user.is_active:
            return _build_account_disabled_response()
        confirm_email(user)
        return build_token_response(user, is_new_user=True)


class EmailLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        request=EmailLoginSerializer,
        responses={
            200: EmailLoginResultSerializer,
            400: ApiErrorSerializer,
            401: ApiErrorSerializer,
            403: ApiErrorSerializer,
        },
        summary="Log in with an email and a password",
    )
    def post(self, request):
        serializer = EmailLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return build_validation_error_response(serializer)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        user = find_user_by_email(email)
        if user is None:
            burn_password_check_time(password)
        if user is None or not user.check_password(password):
            return build_error_response(
                "invalid_credentials",
                "Невірний email або пароль.",
                status.HTTP_401_UNAUTHORIZED,
            )
        # Only a person who knows the password learns the state of the account.
        if not user.is_active:
            return _build_account_disabled_response()
        if not user.is_email_verified:
            return build_error_response(
                "email_not_verified",
                "Email ще не підтверджено. Введіть код із листа "
                "або запросіть новий.",
                status.HTTP_403_FORBIDDEN,
            )
        return build_token_response(user, is_new_user=False)


def _issue_email_code(request, email):
    return issue_code(
        CodePurpose.EMAIL_VERIFICATION,
        email,
        ip_address=_read_client_ip(request),
    )


def _queue_email_code(email, code):
    """Hand the letter to Celery; return an error response if it cannot."""
    try:
        send_email_code.delay(email, code)
    except OperationalError:
        return build_error_response(
            "email_unavailable",
            "Не вдалося надіслати лист. Спробуйте трохи пізніше.",
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return None


def _build_issue_error_response(error):
    if isinstance(error, CodeResendTooSoonError):
        return build_error_response(
            "code_resend_too_soon",
            f"Новий код можна запросити через {error.retry_after_seconds} с.",
            status.HTTP_429_TOO_MANY_REQUESTS,
            retry_after_seconds=error.retry_after_seconds,
        )
    minutes = math.ceil(error.retry_after_seconds / 60)
    return build_error_response(
        "code_request_limit",
        f"Забагато запитів коду. Спробуйте через {minutes} хв.",
        status.HTTP_429_TOO_MANY_REQUESTS,
        retry_after_seconds=error.retry_after_seconds,
    )


def _build_account_disabled_response():
    return build_error_response(
        "account_disabled",
        "Обліковий запис вимкнено.",
        status.HTTP_403_FORBIDDEN,
    )


def _read_client_ip(request):
    # The same address the throttles use, so both limits see one client.
    identity = CodeIpThrottle().get_ident(request)
    try:
        return str(ipaddress.ip_address(identity))
    except ValueError:
        return None
