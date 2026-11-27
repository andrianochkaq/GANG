"""Checks of the bundled catalog file itself; no database needed."""

import json
from collections import Counter

import pytest

from apps.products.models import ProductUnit
from apps.products.services.catalog_loader import DEFAULT_CATALOG_PATH

EXPECTED_CATEGORY_SLUGS = {
    "dairy",
    "meat-fish",
    "vegetables",
    "fruits",
    "grains-pasta",
    "bakery",
    "drinks",
    "sauces-spices",
    "frozen",
    "sweets",
    "other",
}


@pytest.fixture(scope="module")
def catalog():
    with DEFAULT_CATALOG_PATH.open(encoding="utf-8") as catalog_file:
        return json.load(catalog_file)


def test_catalog_has_the_eleven_categories(catalog):
    slugs = [category["slug"] for category in catalog["categories"]]

    assert set(slugs) == EXPECTED_CATEGORY_SLUGS
    assert len(slugs) == len(EXPECTED_CATEGORY_SLUGS)


def test_catalog_has_about_five_hundred_products(catalog):
    assert 450 <= len(catalog["products"]) <= 600


def test_every_category_has_products(catalog):
    counts = Counter(product["category"] for product in catalog["products"])

    assert set(counts) == EXPECTED_CATEGORY_SLUGS
    assert min(counts.values()) >= 10


def test_product_names_are_unique_ignoring_case(catalog):
    names = [product["name"].casefold() for product in catalog["products"]]

    assert len(names) == len(set(names))


def test_names_are_ukrainian_sentences_starting_with_a_capital(catalog):
    for product in catalog["products"]:
        assert product["name"][0].isupper(), product["name"]
        assert product["name"] == product["name"].strip()


def test_aliases_are_lowercase_and_do_not_repeat_the_name(catalog):
    for product in catalog["products"]:
        assert len(product["aliases"]) == len(set(product["aliases"]))
        for alias in product["aliases"]:
            assert alias == alias.lower(), product["name"]
            assert alias != product["name"].lower(), product["name"]


def test_units_are_known_units(catalog):
    units = {unit.value for unit in ProductUnit}

    for product in catalog["products"]:
        assert product["default_unit"] in units, product["name"]


def test_products_counted_in_pieces_have_grams_per_piece(catalog):
    for product in catalog["products"]:
        if product["default_unit"] == ProductUnit.PIECE:
            assert product["grams_per_piece"], product["name"]


def test_nutrition_is_plausible(catalog):
    for product in catalog["products"]:
        protein = product["protein_per_100g"]
        fat = product["fat_per_100g"]
        carbs = product["carbs_per_100g"]
        assert 0 <= product["kcal_per_100g"] <= 900, product["name"]
        assert protein + fat + carbs <= 100, product["name"]


def test_shelf_days_are_positive_whole_numbers(catalog):
    for product in catalog["products"]:
        assert isinstance(product["default_shelf_days"], int), product["name"]
        assert product["default_shelf_days"] >= 1, product["name"]
