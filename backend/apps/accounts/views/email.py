"""Endpoints to register and log in by email with a confirmation code."""

from django.contrib.auth.models import update_last_login
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response

from apps.accounts.serializers import (
    ApiErrorSerializer,
    EmailCodeSentSerializer,
    EmailLoginSerializer,
    EmailRegisterSerializer,
    EmailResendCodeSerializer,
    EmailVerifySerializer,
    TokenPairSerializer,
)
from apps.accounts.services.codes import RESEND_COOLDOWN_SECONDS
from apps.accounts.services.email_auth import (
    authenticate_email_user,
    resend_email_code,
    start_email_registration,
    verify_email_code,
)
from apps.accounts.services.tokens import issue_token_pair
from apps.accounts.tasks import send_email_code
from apps.accounts.throttles import CodeIpThrottle, CodeTargetThrottle
from apps.accounts.views.base import AuthApiView, get_client_ip_address


class EmailRegisterView(AuthApiView):
    throttle_classes = [CodeIpThrottle, CodeTargetThrottle]

    @extend_schema(
        request=EmailRegisterSerializer,
        responses={
            201: EmailCodeSentSerializer,
            400: ApiErrorSerializer,
            409: ApiErrorSerializer,
            429: ApiErrorSerializer,
        },
        summary="Register by email and send a confirmation code",
    )
    def post(self, request):
        serializer = EmailRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        code = start_email_registration(
            email,
            password,
            ip_address=get_client_ip_address(request),
        )
        send_email_code.delay(email, code)
        return Response(_build_code_sent_body(email), status=status.HTTP_201_CREATED)


class EmailResendCodeView(AuthApiView):
    throttle_classes = [CodeIpThrottle, CodeTargetThrottle]

    @extend_schema(
        request=EmailResendCodeSerializer,
        responses={
            202: EmailCodeSentSerializer,
            400: ApiErrorSerializer,
            429: ApiErrorSerializer,
        },
        summary="Send a new confirmation code",
    )
    def post(self, request):
        serializer = EmailResendCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        code = resend_email_code(email, ip_address=get_client_ip_address(request))
        if code is not None:
            send_email_code.delay(email, code)
        # The same answer for every email: it does not tell who has an account.
        body = _build_code_sent_body(email)
        return Response(body, status=status.HTTP_202_ACCEPTED)


class EmailVerifyView(AuthApiView):
    @extend_schema(
        request=EmailVerifySerializer,
        responses={
            200: TokenPairSerializer,
            400: ApiErrorSerializer,
        },
        summary="Confirm the email with a code and sign in",
    )
    def post(self, request):
        serializer = EmailVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]
        user = verify_email_code(email, code)
        return _build_session_response(user)


class EmailLoginView(AuthApiView):
    @extend_schema(
        request=EmailLoginSerializer,
        responses={
            200: TokenPairSerializer,
            400: ApiErrorSerializer,
            401: ApiErrorSerializer,
            403: ApiErrorSerializer,
        },
        summary="Log in by email and password",
    )
    def post(self, request):
        serializer = EmailLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        user = authenticate_email_user(email, password)
        return _build_session_response(user)


def _build_code_sent_body(email):
    return {"email": email, "resend_after_seconds": RESEND_COOLDOWN_SECONDS}


def _build_session_response(user):
    update_last_login(None, user)
    return Response(issue_token_pair(user), status=status.HTTP_200_OK)
