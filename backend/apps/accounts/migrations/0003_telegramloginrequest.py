import uuid

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_onetimecode"),
    ]

    operations = [
        migrations.CreateModel(
            name="TelegramLoginRequest",
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
                ("token", models.CharField(max_length=64, unique=True)),
                ("telegram_id", models.BigIntegerField(blank=True, null=True)),
                ("confirmed_at", models.DateTimeField(blank=True, null=True)),
                ("is_used", models.BooleanField(default=False)),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("expires_at", models.DateTimeField()),
            ],
        ),
    ]
