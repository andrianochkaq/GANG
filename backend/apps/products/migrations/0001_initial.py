import uuid

import django.contrib.postgres.indexes
import django.core.validators
import django.db.models.deletion
from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations, models

import apps.products.validators


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        TrigramExtension(),
        migrations.CreateModel(
            name="Category",
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
                ("slug", models.SlugField(max_length=40, unique=True)),
                ("name", models.CharField(max_length=60, unique=True)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                "verbose_name_plural": "categories",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.CreateModel(
            name="CatalogProduct",
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
                ("name", models.CharField(max_length=120, unique=True)),
                (
                    "aliases",
                    models.JSONField(
                        blank=True,
                        default=list,
                        validators=[apps.products.validators.validate_aliases],
                    ),
                ),
                (
                    "default_unit",
                    models.CharField(
                        choices=[
                            ("g", "г"),
                            ("kg", "кг"),
                            ("ml", "мл"),
                            ("l", "л"),
                            ("pcs", "шт"),
                            ("pack", "уп"),
                        ],
                        default="g",
                        max_length=4,
                    ),
                ),
                (
                    "kcal_per_100g",
                    models.DecimalField(
                        decimal_places=1,
                        max_digits=4,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(900),
                        ],
                    ),
                ),
                (
                    "protein_per_100g",
                    models.DecimalField(
                        decimal_places=1,
                        max_digits=4,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ],
                    ),
                ),
                (
                    "fat_per_100g",
                    models.DecimalField(
                        decimal_places=1,
                        max_digits=4,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ],
                    ),
                ),
                (
                    "carbs_per_100g",
                    models.DecimalField(
                        decimal_places=1,
                        max_digits=4,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ],
                    ),
                ),
                (
                    "default_shelf_days",
                    models.PositiveSmallIntegerField(
                        validators=[django.core.validators.MinValueValidator(1)]
                    ),
                ),
                (
                    "grams_per_piece",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        null=True,
                        validators=[django.core.validators.MinValueValidator(1)],
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="products",
                        to="products.category",
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.AddIndex(
            model_name="catalogproduct",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["name"],
                name="catalog_product_name_trgm",
                opclasses=["gin_trgm_ops"],
            ),
        ),
    ]
