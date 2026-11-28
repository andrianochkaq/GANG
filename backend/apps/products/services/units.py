"""Unit conversion for stock changes.

Supported conversions:

* g <-> kg and ml <-> l, always;
* pieces <-> grams, from the catalog product's ``grams_per_piece``;
* ml <-> g, from the catalog product's ``density_g_per_ml``;
* pieces <-> ml, through both of the above.

Packs (``pack``) have no known size, so they convert only to themselves.
Anything else raises ``UnitConversionError``: nothing is ever guessed.
Results are rounded to three decimal places, like stored quantities.
"""

from decimal import ROUND_HALF_UP, Decimal

from apps.products.models import ProductUnit

QUANTITY_STEP = Decimal("0.001")

_GRAMS_PER_UNIT = {
    ProductUnit.GRAM: Decimal(1),
    ProductUnit.KILOGRAM: Decimal(1000),
}
_MILLILITERS_PER_UNIT = {
    ProductUnit.MILLILITER: Decimal(1),
    ProductUnit.LITER: Decimal(1000),
}


class UnitConversionError(Exception):
    """The amount cannot be converted between these units."""

    def __init__(self, from_unit, to_unit):
        super().__init__(f"Cannot convert {from_unit} to {to_unit}.")
        self.from_unit = from_unit
        self.to_unit = to_unit


def convert_quantity(amount, from_unit, to_unit, catalog_product=None):
    """Return ``amount`` of ``from_unit`` expressed in ``to_unit``."""
    if from_unit == to_unit:
        return amount
    grams = _to_grams(amount, from_unit, to_unit, catalog_product)
    result = _from_grams(grams, from_unit, to_unit, catalog_product)
    return result.quantize(QUANTITY_STEP, rounding=ROUND_HALF_UP)


def _to_grams(amount, from_unit, to_unit, catalog_product):
    if from_unit in _GRAMS_PER_UNIT:
        return amount * _GRAMS_PER_UNIT[from_unit]
    if from_unit in _MILLILITERS_PER_UNIT:
        density = _get_density(catalog_product, from_unit, to_unit)
        return amount * _MILLILITERS_PER_UNIT[from_unit] * density
    if from_unit == ProductUnit.PIECE:
        return amount * _get_grams_per_piece(catalog_product, from_unit, to_unit)
    raise UnitConversionError(from_unit, to_unit)


def _from_grams(grams, from_unit, to_unit, catalog_product):
    if to_unit in _GRAMS_PER_UNIT:
        return grams / _GRAMS_PER_UNIT[to_unit]
    if to_unit in _MILLILITERS_PER_UNIT:
        density = _get_density(catalog_product, from_unit, to_unit)
        return grams / density / _MILLILITERS_PER_UNIT[to_unit]
    if to_unit == ProductUnit.PIECE:
        return grams / _get_grams_per_piece(catalog_product, from_unit, to_unit)
    raise UnitConversionError(from_unit, to_unit)


def _get_density(catalog_product, from_unit, to_unit):
    density = getattr(catalog_product, "density_g_per_ml", None)
    if not density:
        raise UnitConversionError(from_unit, to_unit)
    return Decimal(density)


def _get_grams_per_piece(catalog_product, from_unit, to_unit):
    grams_per_piece = getattr(catalog_product, "grams_per_piece", None)
    if not grams_per_piece:
        raise UnitConversionError(from_unit, to_unit)
    return Decimal(grams_per_piece)
