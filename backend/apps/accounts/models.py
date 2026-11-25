"""Accounts models: the custom user.

A person signs in with an email, a phone number or a Telegram account, so
none of the three is required on its own. Every user needs at least one
of them, and a database constraint enforces that.
"""

import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .validators import validate_phone_number


class Gender(models.TextChoices):
    """Sets the grammatical form of Ukrainian texts and the calorie formula."""

    FEMALE = "female", "Жіноча"
    MALE = "male", "Чоловіча"
    UNSET = "unset", "Не вказано"


class ThemeColor(models.TextChoices):
    """The 17 app colours of the design system (docs/design-system)."""

    WHITE = "white", "Білий"
    OCEAN = "ocean", "Океан"
    SKY = "sky", "Небо"
    LILAC = "lilac", "Бузок"
    LAVENDER = "lavender", "Лаванда"
    EMERALD = "emerald", "Смарагд"
    SUMMER = "summer", "Літо"
    SPROUT = "sprout", "Паросток"
    LIME = "lime", "Лайм"
    CINNAMON = "cinnamon", "Кориця"
    SUNSET = "sunset", "Захід"
    PEACH = "peach", "Персик"
    LEMON = "lemon", "Лимон"
    BURGUNDY = "burgundy", "Бургунді"
    CHERRY = "cherry", "Вишня"
    SAKURA = "sakura", "Сакура"
    FOG = "fog", "Туман"


class CodePurpose(models.TextChoices):
    """What a one-time code is for."""

    EMAIL_VERIFICATION = "email_verification", "Підтвердження email"
    PHONE_LOGIN = "phone_login", "Вхід за телефоном"
    TELEGRAM_LOGIN = "telegram_login", "Вхід через Telegram"


class UserManager(BaseUserManager):
    """Creates users that are identified by their nickname."""

    def create_user(self, nickname, password=None, **extra_fields):
        return self._create_user(nickname, password, **extra_fields)

    def create_superuser(self, nickname, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields["is_staff"] is not True:
            raise ValueError("A superuser must have is_staff=True.")
        if extra_fields["is_superuser"] is not True:
            raise ValueError("A superuser must have is_superuser=True.")
        if not password:
            raise ValueError("A superuser must have a password.")
        return self._create_user(nickname, password, **extra_fields)

    def _create_user(self, nickname, password, **extra_fields):
        if not nickname:
            raise ValueError("The nickname must be set.")
        user = self.model(
            nickname=self.model.normalize_username(nickname),
            **extra_fields,
        )
        if password:
            user.set_password(password)
        else:
            # Passwordless login (email code, SMS code, Telegram): no password.
            user.password = None
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(
        max_length=16,
        unique=True,
        null=True,
        blank=True,
        validators=[validate_phone_number],
    )
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    # A password is optional because two of the three logins have none.
    password = models.CharField(_("password"), max_length=128, null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)
    name = models.CharField(max_length=100, blank=True)
    # Shown in invitations and member lists.
    nickname = models.CharField(
        max_length=30,
        unique=True,
        validators=[UnicodeUsernameValidator()],
    )
    gender = models.CharField(
        max_length=6,
        choices=Gender.choices,
        default=Gender.UNSET,
    )
    theme_color = models.CharField(
        max_length=16,
        choices=ThemeColor.choices,
        default=ThemeColor.WHITE,
    )
    is_onboarding_done = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = "nickname"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(email__isnull=False)
                    | models.Q(phone__isnull=False)
                    | models.Q(telegram_id__isnull=False)
                ),
                name="accounts_user_has_contact",
            ),
            # An empty string would count as a contact and clash with the
            # unique rule, so "no value" is always NULL.
            models.CheckConstraint(
                condition=~models.Q(email=""),
                name="accounts_user_email_not_blank",
            ),
            models.CheckConstraint(
                condition=~models.Q(phone=""),
                name="accounts_user_phone_not_blank",
            ),
        ]

    def __str__(self):
        return self.nickname

    def save(self, *args, **kwargs):
        self._normalize_contacts()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        self._normalize_contacts()
        if self.email is None and self.phone is None and self.telegram_id is None:
            raise ValidationError(
                "Вкажіть хоча б одне: email, телефон або Telegram.",
                code="contact_required",
            )

    def check_password(self, raw_password):
        if self.password is None:
            return False
        return super().check_password(raw_password)

    def has_usable_password(self):
        return self.password is not None and super().has_usable_password()

    def _normalize_contacts(self):
        email = (self.email or "").strip()
        self.email = UserManager.normalize_email(email) or None
        self.phone = (self.phone or "").strip() or None


class OneTimeCode(models.Model):
    """A 6-digit code sent to an email, a phone or a Telegram account.

    Only a keyed hash of the code is stored, never the code itself. The
    rules (10 minutes, 5 attempts, resend and hourly limits) live in
    ``apps.accounts.services.codes``. Rows are kept for an hour after they
    are created, because the hourly request limits count them.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    purpose = models.CharField(max_length=20, choices=CodePurpose.choices)
    # The email, phone number or Telegram id the code was sent to, normalized.
    target = models.CharField(max_length=254)
    code_hash = models.CharField(max_length=64)
    # Who asked for the code; empty when it was requested without a request.
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    attempt_count = models.PositiveSmallIntegerField(default=0)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(
                fields=["target", "created_at"],
                name="accounts_code_target_idx",
            ),
            models.Index(
                fields=["ip_address", "created_at"],
                name="accounts_code_ip_idx",
            ),
        ]

    def __str__(self):
        return f"{self.purpose} code for {self.target}"
