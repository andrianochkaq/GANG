import uuid

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="OneTimeCode",
            fields=[
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
                    "purpose",
                    models.CharField(
                        choices=[
                            ("email_verification", "Підтвердження email"),
                            ("phone_login", "Вхід за телефоном"),
                            ("telegram_login", "Вхід через Telegram"),
                        ],
                        max_length=20,
                    ),
                ),
                ("target", models.CharField(max_length=254)),
                ("code_hash", models.CharField(max_length=64)),
                (
                    "ip_address",
                    models.GenericIPAddressField(blank=True, null=True),
                ),
                ("attempt_count", models.PositiveSmallIntegerField(default=0)),
                ("is_used", models.BooleanField(default=False)),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("expires_at", models.DateTimeField()),
            ],
        ),
        migrations.AddIndex(
            model_name="onetimecode",
            index=models.Index(
                fields=["target", "created_at"],
                name="accounts_code_target_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="onetimecode",
            index=models.Index(
                fields=["ip_address", "created_at"],
                name="accounts_code_ip_idx",
            ),
        ),
    ]
