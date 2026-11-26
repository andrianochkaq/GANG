"""Serializers of the accounts API."""

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.accounts.models import User
from apps.accounts.services.codes import CODE_LENGTH
from apps.accounts.validators import normalize_phone_number


class PhoneCodeRequestSerializer(serializers.Serializer):
    """The phone number a login code is requested for."""

    phone = serializers.CharField(max_length=32)

    def validate_phone(self, value):
        try:
            return normalize_phone_number(value)
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                error.messages[0],
                code=error.code,
            ) from error


class PhoneLoginSerializer(PhoneCodeRequestSerializer):
    """A phone number and the code that was sent to it. No password."""

    code = serializers.RegexField(
        regex=rf"^[0-9]{{{CODE_LENGTH}}}$",
        error_messages={"invalid": f"Введіть код із {CODE_LENGTH} цифр."},
    )


class PhoneCodeSentSerializer(serializers.Serializer):
    resend_after_seconds = serializers.IntegerField()


class PhoneLoginResultSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()
    is_new_user = serializers.BooleanField()


class EmailCodeRequestSerializer(serializers.Serializer):
    """The email a confirmation code is requested for."""

    email = serializers.EmailField(max_length=254)

    def validate_email(self, value):
        return value.strip().lower()


class EmailRegisterSerializer(EmailCodeRequestSerializer):
    """An email and a password. The password goes through Django validators."""

    password = serializers.CharField(
        max_length=128,
        write_only=True,
        trim_whitespace=False,
    )

    def validate(self, attrs):
        # The user is not saved: the similarity validator only reads it.
        candidate = User(email=attrs["email"])
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                {"password": list(error.messages)},
            ) from error
        return attrs


class EmailLoginSerializer(EmailCodeRequestSerializer):
    """An email and a password. They are checked by the view, not here."""

    password = serializers.CharField(
        max_length=128,
        write_only=True,
        trim_whitespace=False,
    )


class EmailVerifySerializer(EmailCodeRequestSerializer):
    """An email and the code that was sent to it."""

    code = serializers.RegexField(
        regex=rf"^[0-9]{{{CODE_LENGTH}}}$",
        error_messages={"invalid": f"Введіть код із {CODE_LENGTH} цифр."},
    )


class EmailCodeSentSerializer(serializers.Serializer):
    resend_after_seconds = serializers.IntegerField()


class EmailLoginResultSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()
    is_new_user = serializers.BooleanField()


class TelegramLoginStartedSerializer(serializers.Serializer):
    token = serializers.CharField()
    deep_link = serializers.URLField()
    expires_in_seconds = serializers.IntegerField()
    poll_interval_seconds = serializers.IntegerField()


class TelegramLoginStatusSerializer(serializers.Serializer):
    """``pending`` until confirmed; then the same body as a phone login."""

    status = serializers.ChoiceField(choices=["pending", "confirmed"])
    refresh = serializers.CharField(required=False)
    access = serializers.CharField(required=False)
    is_new_user = serializers.BooleanField(required=False)


class ApiErrorSerializer(serializers.Serializer):
    """The error body every endpoint returns (docs/architecture.md, 5.4)."""

    code = serializers.CharField()
    detail = serializers.CharField()
    fields = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()),
    )
