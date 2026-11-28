import uuid

import django.contrib.postgres.indexes
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("fridges", "0001_initial"),
        ("products", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FridgeItem",
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
                ("name", models.CharField(max_length=120)),
                (
                    "quantity",
                    models.DecimalField(decimal_places=3, max_digits=12),
                ),
                (
                    "unit",
                    models.CharField(
                        choices=[
                            ("g", "г"),
                            ("kg", "кг"),
                            ("ml", "мл"),
                            ("l", "л"),
                            ("pcs", "шт"),
                            ("pack", "уп"),
                        ],
                        max_length=4,
                    ),
                ),
                ("expires_at", models.DateField(blank=True, null=True)),
                ("opened_at", models.DateField(blank=True, null=True)),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "added_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "catalog_product",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="fridge_items",
                        to="products.catalogproduct",
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="fridge_items",
                        to="products.category",
                    ),
                ),
                (
                    "fridge",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="fridges.fridge",
                    ),
                ),
            ],
            options={
                "ordering": ["name", "id"],
            },
        ),
        migrations.CreateModel(
            name="StockMovement",
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
                ("item_name", models.CharField(max_length=120)),
                (
                    "unit",
                    models.CharField(
                        choices=[
                            ("g", "г"),
                            ("kg", "кг"),
                            ("ml", "мл"),
                            ("l", "л"),
                            ("pcs", "шт"),
                            ("pack", "уп"),
                        ],
                        max_length=4,
                    ),
                ),
                ("delta", models.DecimalField(decimal_places=3, max_digits=12)),
                (
                    "quantity_after",
                    models.DecimalField(decimal_places=3, max_digits=12),
                ),
                (
                    "reason",
                    models.CharField(
                        choices=[
                            ("manual", "Вручну"),
                            ("calories", "Підрахунок калорій"),
                            ("recipe", "Рецепт"),
                            ("receipt", "Чек"),
                            ("shopping", "Список покупок"),
                        ],
                        max_length=8,
                    ),
                ),
                ("at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "fridge",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="stock_movements",
                        to="fridges.fridge",
                    ),
                ),
                (
                    "item",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="movements",
                        to="products.fridgeitem",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-at", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="fridgeitem",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["name"],
                name="fridge_item_name_trgm",
                opclasses=["gin_trgm_ops"],
            ),
        ),
        migrations.AddConstraint(
            model_name="fridgeitem",
            constraint=models.CheckConstraint(
                condition=models.Q(("quantity__gt", 0)),
                name="products_fridgeitem_quantity_positive",
            ),
        ),
        migrations.AddConstraint(
            model_name="stockmovement",
            constraint=models.CheckConstraint(
                condition=models.Q(("quantity_after__gte", 0)),
                name="products_stockmovement_quantity_after_not_negative",
            ),
        ),
    ]
