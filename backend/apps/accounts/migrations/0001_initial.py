import uuid

import django.contrib.auth.validators
from django.db import migrations, models

import apps.accounts.validators


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "password",
                    models.CharField(
                        blank=True,
                        max_length=128,
                        null=True,
                        verbose_name="password",
                    ),
                ),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="last login",
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        blank=True,
                        max_length=254,
                        null=True,
                        unique=True,
                    ),
                ),
                (
                    "phone",
                    models.CharField(
                        blank=True,
                        max_length=16,
                        null=True,
                        unique=True,
                        validators=[apps.accounts.validators.validate_phone_number],
                    ),
                ),
                (
                    "telegram_id",
                    models.BigIntegerField(blank=True, null=True, unique=True),
                ),
                ("is_email_verified", models.BooleanField(default=False)),
                ("name", models.CharField(blank=True, max_length=100)),
                (
                    "nickname",
                    models.CharField(
                        max_length=30,
                        unique=True,
                        validators=[
                            django.contrib.auth.validators.UnicodeUsernameValidator()
                        ],
                    ),
                ),
                (
                    "gender",
                    models.CharField(
                        choices=[
                        ("female", "Жіноча"),
                        ("male", "Чоловіча"),
                        ("unset", "Не вказано"),
                    ],
                        default="unset",
                        max_length=6,
                    ),
                ),
                (
                    "theme_color",
                    models.CharField(
                        choices=[
                        ("white", "Білий"),
                        ("ocean", "Океан"),
                        ("sky", "Небо"),
                        ("lilac", "Бузок"),
                        ("lavender", "Лаванда"),
                        ("emerald", "Смарагд"),
                        ("summer", "Літо"),
                        ("sprout", "Паросток"),
                        ("lime", "Лайм"),
                        ("cinnamon", "Кориця"),
                        ("sunset", "Захід"),
                        ("peach", "Персик"),
                        ("lemon", "Лимон"),
                        ("burgundy", "Бургунді"),
                        ("cherry", "Вишня"),
                        ("sakura", "Сакура"),
                        ("fog", "Туман"),
                    ],
                        default="white",
                        max_length=16,
                    ),
                ),
                ("is_onboarding_done", models.BooleanField(default=False)),
                ("is_staff", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                condition=models.Q(("email__isnull", False))
                | models.Q(("phone__isnull", False))
                | models.Q(("telegram_id__isnull", False)),
                name="accounts_user_has_contact",
            ),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                condition=models.Q(("email", ""), _negated=True),
                name="accounts_user_email_not_blank",
            ),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                condition=models.Q(("phone", ""), _negated=True),
                name="accounts_user_phone_not_blank",
            ),
        ),
    ]
