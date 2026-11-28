"""Products models: the shared catalog and the food in each fridge.

The catalog belongs to nobody: every fridge picks products from it. A
catalog product knows its category, the unit it is usually counted in,
its nutrition per 100 g and how long it usually keeps. Product names are
searched by similarity, so ``name`` has a trigram index (the ``pg_trgm``
extension is enabled in the first migration).

A fridge item is one product in one fridge. Its quantity is never zero or
negative: an item that is used up is removed. Every change of quantity is
written to ``StockMovement``, which outlives the item (rules live in
``services/stock.py``).
"""

import uuid

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

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


class StockReason(models.TextChoices):
    """Why a quantity changed."""

    MANUAL = "manual", "Вручну"
    CALORIES = "calories", "Підрахунок калорій"
    RECIPE = "recipe", "Рецепт"
    RECEIPT = "receipt", "Чек"
    SHOPPING = "shopping", "Список покупок"


class FridgeItem(models.Model):
    """One product in one fridge, with how much of it is left."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fridge = models.ForeignKey(
        "fridges.Fridge",
        on_delete=models.CASCADE,
        related_name="items",
    )
    name = models.CharField(max_length=120)
    catalog_product = models.ForeignKey(
        CatalogProduct,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fridge_items",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="fridge_items",
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    unit = models.CharField(max_length=4, choices=ProductUnit.choices)
    expires_at = models.DateField(null=True, blank=True)
    opened_at = models.DateField(null=True, blank=True)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["name", "id"]
        indexes = [
            GinIndex(
                fields=["name"],
                name="fridge_item_name_trgm",
                opclasses=["gin_trgm_ops"],
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="products_fridgeitem_quantity_positive",
            ),
        ]

    def __str__(self):
        return self.name


class StockMovement(models.Model):
    """One change of quantity. It stays after the item is removed.

    ``item_name`` and ``unit`` are copied from the item, so the history
    still reads well once the item is gone (``item`` is then empty).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fridge = models.ForeignKey(
        "fridges.Fridge",
        on_delete=models.CASCADE,
        related_name="stock_movements",
    )
    item = models.ForeignKey(
        FridgeItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movements",
    )
    item_name = models.CharField(max_length=120)
    unit = models.CharField(max_length=4, choices=ProductUnit.choices)
    delta = models.DecimalField(max_digits=12, decimal_places=3)
    quantity_after = models.DecimalField(max_digits=12, decimal_places=3)
    reason = models.CharField(max_length=8, choices=StockReason.choices)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity_after__gte=0),
                name="products_stockmovement_quantity_after_not_negative",
            ),
        ]

    def __str__(self):
        return f"{self.item_name}: {self.delta}"
