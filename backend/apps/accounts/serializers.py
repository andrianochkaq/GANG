"""Request and response bodies of the email sign-in endpoints."""

from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.accounts.models import User
from apps.accounts.services.codes import CODE_LENGTH

EMAIL_MAX_LENGTH = 254
PASSWORD_MAX_LENGTH = 128


class NormalizedEmailField(serializers.EmailField):
    """An email that is trimmed and lowercased: one person, one account."""

    def to_internal_value(self, data):
        return super().to_internal_value(data).lower()


class EmailRegisterSerializer(serializers.Serializer):
    email = NormalizedEmailField(max_length=EMAIL_MAX_LENGTH)
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        max_length=PASSWORD_MAX_LENGTH,
    )

    def validate(self, attrs):
        candidate = User(email=attrs["email"])
        try:
            password_validation.validate_password(attrs["password"], candidate)
        except DjangoValidationError as error:
            messages = list(error.messages)
            raise serializers.ValidationError({"password": messages}) from error
        return attrs


class EmailVerifySerializer(serializers.Serializer):
    email = NormalizedEmailField(max_length=EMAIL_MAX_LENGTH)
    code = serializers.CharField(min_length=CODE_LENGTH, max_length=CODE_LENGTH)

    def validate_code(self, value):
        if not (value.isascii() and value.isdigit()):
            raise serializers.ValidationError("Код складається лише з цифр.")
        return value


class EmailResendCodeSerializer(serializers.Serializer):
    email = NormalizedEmailField(max_length=EMAIL_MAX_LENGTH)


class EmailLoginSerializer(serializers.Serializer):
    email = NormalizedEmailField(max_length=EMAIL_MAX_LENGTH)
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        max_length=PASSWORD_MAX_LENGTH,
    )


class EmailCodeSentSerializer(serializers.Serializer):
    """Documents the answer of the endpoints that send a code."""

    email = serializers.EmailField()
    resend_after_seconds = serializers.IntegerField()


class TokenPairSerializer(serializers.Serializer):
    """Documents the answer of the endpoints that sign a person in."""

    access = serializers.CharField()
    refresh = serializers.CharField()


class ApiErrorSerializer(serializers.Serializer):
    """Documents the error body shared by the account endpoints.

    Validation errors also carry ``fields``: a list of messages per field.
    """

    code = serializers.CharField()
    detail = serializers.CharField()
