from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.models import ProtectedError

from apps.products.models import CatalogProduct, Category, ProductUnit

pytestmark = pytest.mark.django_db


def make_category(slug="dairy", name="Молочне", sort_order=0):
    return Category.objects.create(slug=slug, name=name, sort_order=sort_order)


def build_product(category, **overrides):
    fields = {
        "name": "Молоко 2,5%",
        "category": category,
        "default_unit": ProductUnit.MILLILITER,
        "kcal_per_100g": Decimal("52"),
        "protein_per_100g": Decimal("2.9"),
        "fat_per_100g": Decimal("2.5"),
        "carbs_per_100g": Decimal("4.8"),
        "default_shelf_days": 7,
    }
    fields.update(overrides)
    return CatalogProduct(**fields)


def test_category_and_product_are_shown_by_name():
    category = make_category()
    product = build_product(category)

    assert str(category) == "Молочне"
    assert str(product) == "Молоко 2,5%"


def test_categories_are_ordered_by_sort_order_then_name():
    make_category(slug="fruits", name="Фрукти", sort_order=1)
    make_category(slug="vegetables", name="Овочі", sort_order=1)
    make_category(slug="dairy", name="Молочне", sort_order=0)

    names = list(Category.objects.values_list("name", flat=True))

    assert names == ["Молочне", "Овочі", "Фрукти"]


def test_a_valid_product_passes_validation_and_is_saved():
    product = build_product(make_category())

    product.full_clean()
    product.save()

    saved = CatalogProduct.objects.get(name="Молоко 2,5%")
    assert saved.aliases == []
    assert saved.grams_per_piece is None
    assert saved.kcal_per_100g == Decimal("52.0")


def test_product_names_are_unique():
    category = make_category()
    build_product(category).save()

    with pytest.raises(IntegrityError), transaction.atomic():
        build_product(category).save()


def test_a_category_with_products_cannot_be_deleted():
    category = make_category()
    build_product(category).save()

    with pytest.raises(ProtectedError):
        category.delete()


def test_a_product_counted_in_pieces_needs_grams_per_piece():
    product = build_product(
        make_category(),
        name="Яйця курячі",
        default_unit=ProductUnit.PIECE,
    )

    with pytest.raises(ValidationError) as error:
        product.full_clean()

    assert "grams_per_piece" in error.value.message_dict


def test_a_product_counted_in_pieces_is_valid_with_grams_per_piece():
    product = build_product(
        make_category(),
        name="Яйця курячі",
        default_unit=ProductUnit.PIECE,
        grams_per_piece=55,
    )

    product.full_clean()


@pytest.mark.parametrize(
    "field_name, value",
    [
        ("kcal_per_100g", Decimal("-1")),
        ("kcal_per_100g", Decimal("901")),
        ("protein_per_100g", Decimal("100.1")),
        ("fat_per_100g", Decimal("-0.1")),
        ("carbs_per_100g", Decimal("100.1")),
        ("default_shelf_days", 0),
        ("grams_per_piece", 0),
    ],
)
def test_numbers_outside_their_range_are_refused(field_name, value):
    fields = {"default_unit": ProductUnit.PIECE, "grams_per_piece": 50}
    fields[field_name] = value
    product = build_product(make_category(), **fields)

    with pytest.raises(ValidationError) as error:
        product.full_clean()

    assert field_name in error.value.message_dict


@pytest.mark.parametrize("aliases", ["молоко", [""], ["  "], [1], ["а" * 121]])
def test_aliases_must_be_a_list_of_short_words(aliases):
    product = build_product(make_category(), aliases=aliases)

    with pytest.raises(ValidationError) as error:
        product.full_clean()

    assert "aliases" in error.value.message_dict


def test_aliases_keep_their_order():
    product = build_product(make_category(), aliases=["молоко", "молочко"])
    product.full_clean()
    product.save()

    product.refresh_from_db()

    assert product.aliases == ["молоко", "молочко"]


def test_product_names_have_a_trigram_index():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT indexdef FROM pg_indexes WHERE indexname = %s",
            ["catalog_product_name_trgm"],
        )
        row = cursor.fetchone()

    assert row is not None
    assert "gin_trgm_ops" in row[0]
