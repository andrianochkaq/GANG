from decimal import Decimal

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0002_fridgeitem_stockmovement"),
    ]

    operations = [
        migrations.AddField(
            model_name="catalogproduct",
            name="density_g_per_ml",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                max_digits=5,
                null=True,
                validators=[django.core.validators.MinValueValidator(Decimal("0.001"))],
            ),
        ),
    ]
