"""Sessions: renew with the refresh token, log out, read the current user.

A refresh token works once. Renewing a session revokes the token that was
sent and returns a new pair; logging out revokes it without a new pair.
The tokens are revoked in the ``token_blacklist`` tables, so a revoked
token stays unusable until it would have expired anyway.
"""

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.serializers import (
    ApiErrorSerializer,
    CurrentUserSerializer,
    RefreshTokenSerializer,
    SessionRefreshResultSerializer,
)
from apps.accounts.views.responses import (
    build_error_response,
    build_validation_error_response,
)


class SessionRefreshView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        request=RefreshTokenSerializer,
        responses={
            200: SessionRefreshResultSerializer,
            400: ApiErrorSerializer,
            401: ApiErrorSerializer,
            403: ApiErrorSerializer,
        },
        summary="Trade a refresh token for a new access and refresh token",
    )
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        if not serializer.is_valid():
            return build_validation_error_response(serializer)
        try:
            # Checks the signature, the expiry, the type and the blacklist.
            refresh = RefreshToken(serializer.validated_data["refresh"])
        except TokenError:
            return _build_session_ended_response()
        user = get_user_model().objects.filter(pk=refresh["user_id"]).first()
        if user is None:
            return _build_session_ended_response()
        if not user.is_active:
            return build_error_response(
                "account_disabled",
                "Обліковий запис вимкнено.",
                status.HTTP_403_FORBIDDEN,
            )
        refresh.blacklist()
        new_refresh = RefreshToken.for_user(user)
        return Response(
            {
                "refresh": str(new_refresh),
                "access": str(new_refresh.access_token),
            }
        )


class LogoutView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        request=RefreshTokenSerializer,
        responses={204: None, 400: ApiErrorSerializer},
        summary="Log out: revoke the refresh token",
    )
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        if not serializer.is_valid():
            return build_validation_error_response(serializer)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError:
            # Expired, revoked or not a token: there is nothing left to
            # revoke, so the person is logged out all the same.
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserView(RetrieveUpdateAPIView):
    serializer_class = CurrentUserSerializer
    # PUT would force every field; the app only ever sends the changed ones.
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return self.request.user

    @extend_schema(
        responses=CurrentUserSerializer,
        summary="Read the current user",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        request=CurrentUserSerializer,
        responses={200: CurrentUserSerializer, 400: ApiErrorSerializer},
        summary="Update the name, nickname, gender, theme color or onboarding",
    )
    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            self.get_object(),
            data=request.data,
            partial=True,
        )
        if not serializer.is_valid():
            return build_validation_error_response(serializer)
        serializer.save()
        return Response(serializer.data)


def _build_session_ended_response():
    return build_error_response(
        "session_ended",
        "Сесію завершено. Увійдіть знову.",
        status.HTTP_401_UNAUTHORIZED,
    )
