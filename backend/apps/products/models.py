"""Products models: the shared catalog of common food products.

The catalog belongs to nobody: every fridge picks products from it. A
catalog product knows its category, the unit it is usually counted in,
its nutrition per 100 g and how long it usually keeps. Product names are
searched by similarity, so ``name`` has a trigram index (the ``pg_trgm``
extension is enabled in the first migration).
"""

import uuid

from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .validators import validate_aliases

MAX_KCAL_PER_100G = 900
MAX_NUTRIENT_GRAMS_PER_100G = 100


class ProductUnit(models.TextChoices):
    """Units a product can be counted in (see docs/architecture.md)."""

    GRAM = "g", "г"
    KILOGRAM = "kg", "кг"
    MILLILITER = "ml", "мл"
    LITER = "l", "л"
    PIECE = "pcs", "шт"
    PACK = "pack", "уп"


class Category(models.Model):
    """A group of catalog products, for example dairy or vegetables."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=60, unique=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


def _build_nutrient_field(maximum):
    """Return a field for an amount per 100 g with one decimal place."""
    return models.DecimalField(
        max_digits=4,
        decimal_places=1,
        validators=[MinValueValidator(0), MaxValueValidator(maximum)],
    )


class CatalogProduct(models.Model):
    """A common product with its Ukrainian name and nutrition per 100 g."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120, unique=True)
    aliases = models.JSONField(
        default=list,
        blank=True,
        validators=[validate_aliases],
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    default_unit = models.CharField(
        max_length=4,
        choices=ProductUnit.choices,
        default=ProductUnit.GRAM,
    )
    kcal_per_100g = _build_nutrient_field(MAX_KCAL_PER_100G)
    protein_per_100g = _build_nutrient_field(MAX_NUTRIENT_GRAMS_PER_100G)
    fat_per_100g = _build_nutrient_field(MAX_NUTRIENT_GRAMS_PER_100G)
    carbs_per_100g = _build_nutrient_field(MAX_NUTRIENT_GRAMS_PER_100G)
    default_shelf_days = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
    )
    grams_per_piece = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            GinIndex(
                fields=["name"],
                name="catalog_product_name_trgm",
                opclasses=["gin_trgm_ops"],
            ),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        if self.default_unit == ProductUnit.PIECE and self.grams_per_piece is None:
            raise ValidationError(
                {"grams_per_piece": "Для штучного продукту вкажіть вагу штуки."}
            )
