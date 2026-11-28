"""Serializers of the fridge items API."""

from decimal import Decimal

from rest_framework import serializers

from .models import CatalogProduct, Category, FridgeItem, ProductUnit, StockReason
from .services.suggestions import SuggestionSource

NAME_MAX_LENGTH = 120
MIN_QUANTITY = Decimal("0.001")
MAX_BULK_ITEMS = 100


def _build_quantity_field():
    return serializers.DecimalField(
        max_digits=10,
        decimal_places=3,
        min_value=MIN_QUANTITY,
    )


def _build_reason_field():
    return serializers.ChoiceField(
        choices=StockReason.choices,
        default=StockReason.MANUAL,
    )


class FridgeItemSerializer(serializers.ModelSerializer):
    """A fridge item as the client sees it."""

    category = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        model = FridgeItem
        fields = [
            "id",
            "name",
            "catalog_product",
            "category",
            "quantity",
            "unit",
            "expires_at",
            "opened_at",
            "added_by",
            "created_at",
        ]
        read_only_fields = fields


class FridgeItemLineSerializer(serializers.Serializer):
    """One product to add. Give a name, a catalog product, or both.

    Without a name the catalog name is used, and without a unit the catalog
    unit. Without a category the product's category is used, or «Інше».
    """

    name = serializers.CharField(max_length=NAME_MAX_LENGTH, required=False)
    catalog_product = serializers.PrimaryKeyRelatedField(
        queryset=CatalogProduct.objects.all(),
        required=False,
        allow_null=True,
    )
    category = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Category.objects.all(),
        required=False,
        allow_null=True,
    )
    quantity = _build_quantity_field()
    unit = serializers.ChoiceField(choices=ProductUnit.choices, required=False)
    expires_at = serializers.DateField(required=False, allow_null=True)
    opened_at = serializers.DateField(required=False, allow_null=True)

    def validate(self, attrs):
        catalog_product = attrs.get("catalog_product")
        errors = {}
        if "name" not in attrs:
            if catalog_product is None:
                errors["name"] = ["Вкажіть назву або виберіть продукт із каталогу."]
            else:
                attrs["name"] = catalog_product.name
        if "unit" not in attrs:
            if catalog_product is None:
                errors["unit"] = ["Вкажіть одиницю виміру."]
            else:
                attrs["unit"] = catalog_product.default_unit
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class FridgeItemCreateSerializer(FridgeItemLineSerializer):
    """A single product to add, with the reason for the new quantity."""

    reason = _build_reason_field()


class FridgeItemBulkSerializer(serializers.Serializer):
    """Several products added together (receipts, shopping lists)."""

    reason = _build_reason_field()
    items = FridgeItemLineSerializer(
        many=True,
        allow_empty=False,
        max_length=MAX_BULK_ITEMS,
    )


class FridgeItemUpdateSerializer(serializers.Serializer):
    """Fields of an item that can change; send only the ones that do.

    A new ``quantity`` is the amount left now and must be above zero; to
    use an item up, consume it or delete it. The unit cannot change.
    """

    name = serializers.CharField(max_length=NAME_MAX_LENGTH, required=False)
    catalog_product = serializers.PrimaryKeyRelatedField(
        queryset=CatalogProduct.objects.all(),
        required=False,
        allow_null=True,
    )
    category = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Category.objects.all(),
        required=False,
    )
    quantity = serializers.DecimalField(
        max_digits=10,
        decimal_places=3,
        min_value=MIN_QUANTITY,
        required=False,
    )
    expires_at = serializers.DateField(required=False, allow_null=True)
    opened_at = serializers.DateField(required=False, allow_null=True)
    reason = _build_reason_field()


class FridgeItemConsumeSerializer(serializers.Serializer):
    """How much to take out of an item."""

    amount = _build_quantity_field()
    reason = _build_reason_field()


class FridgeItemBulkResponseSerializer(serializers.Serializer):
    items = FridgeItemSerializer(many=True)


class UseFirstListSerializer(serializers.Serializer):
    """Up to 50 items, the most urgent first."""

    items = FridgeItemSerializer(many=True)


class FridgeItemConsumeResponseSerializer(serializers.Serializer):
    """The item after the change; empty when it was used up and removed."""

    removed = serializers.BooleanField()
    item = FridgeItemSerializer(allow_null=True)


class ProductSuggestionQuerySerializer(serializers.Serializer):
    """The text typed so far; no text gives no suggestions."""

    q = serializers.CharField(
        max_length=NAME_MAX_LENGTH,
        allow_blank=True,
        default="",
    )


class ProductSuggestionSerializer(serializers.Serializer):
    """One name offered while typing.

    ``source`` says whether the fridge already has it. ``unit``, ``category``
    (a slug) and ``catalog_product`` are what the add request needs.
    """

    source = serializers.ChoiceField(choices=SuggestionSource.choices)
    name = serializers.CharField()
    unit = serializers.ChoiceField(choices=ProductUnit.choices)
    category = serializers.CharField()
    catalog_product = serializers.UUIDField(allow_null=True)


class ProductSuggestionListSerializer(serializers.Serializer):
    suggestions = ProductSuggestionSerializer(many=True)
