from decimal import Decimal

import pytest

from apps.fridges.services import create_fridge
from apps.products.models import FridgeItem, StockMovement
from apps.products.services.stock import QuantityBelowZeroError, consume_item
from apps.products.services.units import UnitConversionError, convert_quantity
from apps.products.tests.factories import (
    make_catalog_product,
    make_category,
    make_item,
    make_user,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def category():
    return make_category("eggs", "Яйця")


@pytest.fixture
def egg(category):
    return make_catalog_product(category, name="Яйце", unit="pcs", grams_per_piece=60)


@pytest.fixture
def milk(category):
    return make_catalog_product(
        category, name="Молоко", unit="ml", density_g_per_ml=Decimal("1.03")
    )


@pytest.fixture
def plain(category):
    return make_catalog_product(category, name="Щось", unit="g")


@pytest.mark.parametrize(
    ("amount", "from_unit", "to_unit", "expected"),
    [
        ("0.5", "kg", "g", "500"),
        ("250", "g", "kg", "0.25"),
        ("1.5", "l", "ml", "1500"),
        ("300", "ml", "l", "0.3"),
        ("7", "g", "g", "7"),
    ],
)
def test_mass_and_volume_convert_without_a_catalog_product(
    amount, from_unit, to_unit, expected
):
    result = convert_quantity(Decimal(amount), from_unit, to_unit)

    assert result == Decimal(expected)


def test_pieces_convert_to_grams_and_back(egg):
    assert convert_quantity(Decimal("2"), "pcs", "g", egg) == Decimal("120")
    assert convert_quantity(Decimal("120"), "g", "pcs", egg) == Decimal("2")
    assert convert_quantity(Decimal("0.12"), "kg", "pcs", egg) == Decimal("2")


def test_milliliters_convert_to_grams_and_back_by_density(milk):
    assert convert_quantity(Decimal("100"), "ml", "g", milk) == Decimal("103")
    assert convert_quantity(Decimal("103"), "g", "ml", milk) == Decimal("100")
    assert convert_quantity(Decimal("1"), "l", "kg", milk) == Decimal("1.03")


def test_pieces_convert_to_milliliters_through_both_factors(category):
    product = make_catalog_product(
        category,
        name="Желе",
        unit="pcs",
        grams_per_piece=50,
        density_g_per_ml=Decimal("1.25"),
    )

    assert convert_quantity(Decimal("5"), "pcs", "ml", product) == Decimal("200")


@pytest.mark.parametrize(
    ("from_unit", "to_unit"),
    [("pcs", "g"), ("g", "pcs"), ("ml", "g"), ("g", "ml"), ("pcs", "ml")],
)
def test_missing_catalog_data_raises_instead_of_guessing(plain, from_unit, to_unit):
    with pytest.raises(UnitConversionError):
        convert_quantity(Decimal("1"), from_unit, to_unit, plain)
    with pytest.raises(UnitConversionError):
        convert_quantity(Decimal("1"), from_unit, to_unit, None)


def test_packs_convert_only_to_themselves(egg):
    assert convert_quantity(Decimal("2"), "pack", "pack", egg) == Decimal("2")
    with pytest.raises(UnitConversionError):
        convert_quantity(Decimal("2"), "pack", "g", egg)
    with pytest.raises(UnitConversionError):
        convert_quantity(Decimal("2"), "g", "pack", egg)


# --- consuming in another unit ---


@pytest.fixture
def user():
    return make_user("anna")


@pytest.fixture
def fridge(user):
    return create_fridge(user, "Дача")


def test_writing_off_pieces_subtracts_the_catalog_weight(fridge, user, category, egg):
    item = make_item(
        fridge, category, name="Яйця", quantity="600", unit="g", catalog_product=egg
    )

    remaining = consume_item(item, user, Decimal("2"), unit="pcs")

    assert remaining.quantity == Decimal("480")
    movement = StockMovement.objects.get()
    assert movement.delta == Decimal("-120")
    assert movement.unit == "g"


def test_writing_off_kilograms_from_an_item_in_grams(fridge, user, category):
    item = make_item(fridge, category, name="Борошно", quantity="1000", unit="g")

    remaining = consume_item(item, user, Decimal("0.5"), unit="kg")

    assert remaining.quantity == Decimal("500")


def test_an_impossible_conversion_changes_nothing(fridge, user, category, plain):
    item = make_item(
        fridge, category, name="Щось", quantity="600", unit="g", catalog_product=plain
    )

    with pytest.raises(UnitConversionError):
        consume_item(item, user, Decimal("2"), unit="pcs")

    assert FridgeItem.objects.get().quantity == Decimal("600")
    assert StockMovement.objects.count() == 0


def test_a_converted_amount_above_the_stock_is_refused(fridge, user, category):
    item = make_item(fridge, category, name="Борошно", quantity="400", unit="g")

    with pytest.raises(QuantityBelowZeroError) as error:
        consume_item(item, user, Decimal("0.5"), unit="kg")

    assert error.value.available == Decimal("400")


def test_an_amount_that_rounds_to_nothing_is_refused(fridge, user, category):
    item = make_item(fridge, category, name="Борошно", quantity="400", unit="kg")

    with pytest.raises(UnitConversionError):
        consume_item(item, user, Decimal("0.001"), unit="g")
