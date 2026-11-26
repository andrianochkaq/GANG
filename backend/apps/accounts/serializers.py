"""Serializers of the accounts API."""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

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
