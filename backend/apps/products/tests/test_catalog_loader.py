import json
from decimal import Decimal

import pytest

from apps.products.models import CatalogProduct, Category
from apps.products.services.catalog_loader import (
    CatalogFileError,
    load_catalog_file,
)

pytestmark = pytest.mark.django_db

DAIRY = {"slug": "dairy", "name": "Молочне", "sort_order": 0}


def build_milk(**overrides):
    entry = {
        "name": "Молоко 2,5%",
        "aliases": ["молоко"],
        "category": "dairy",
        "default_unit": "ml",
        "kcal_per_100g": 52,
        "protein_per_100g": 2.9,
        "fat_per_100g": 2.5,
        "carbs_per_100g": 4.8,
        "default_shelf_days": 7,
        "grams_per_piece": None,
    }
    entry.update(overrides)
    return entry


def write_catalog(tmp_path, products, categories=None):
    path = tmp_path / "catalog.json"
    catalog = {
        "categories": [DAIRY] if categories is None else categories,
        "products": products,
    }
    path.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
    return path


def test_load_creates_categories_and_products(tmp_path):
    path = write_catalog(tmp_path, [build_milk()])

    result = load_catalog_file(path)

    milk = CatalogProduct.objects.get(name="Молоко 2,5%")
    assert result.categories_created == 1
    assert result.products_created == 1
    assert milk.category.slug == "dairy"
    assert milk.aliases == ["молоко"]
    assert milk.protein_per_100g == Decimal("2.9")
    assert milk.grams_per_piece is None


def test_loading_the_same_file_again_changes_nothing(tmp_path):
    path = write_catalog(tmp_path, [build_milk()])
    load_catalog_file(path)
    milk_id = CatalogProduct.objects.get().pk

    result = load_catalog_file(path)

    assert result.categories_created == 0
    assert result.categories_updated == 0
    assert result.products_created == 0
    assert result.products_updated == 0
    assert result.products_unchanged == 1
    assert CatalogProduct.objects.get().pk == milk_id


def test_changed_values_update_the_existing_product(tmp_path):
    load_catalog_file(write_catalog(tmp_path, [build_milk()]))
    milk_id = CatalogProduct.objects.get().pk
    changed = write_catalog(
        tmp_path,
        [build_milk(kcal_per_100g=53, aliases=["молоко", "молочко"])],
    )

    result = load_catalog_file(changed)

    milk = CatalogProduct.objects.get()
    assert result.products_updated == 1
    assert result.products_created == 0
    assert milk.pk == milk_id
    assert milk.kcal_per_100g == 53
    assert milk.aliases == ["молоко", "молочко"]


def test_changed_category_names_are_updated(tmp_path):
    load_catalog_file(write_catalog(tmp_path, [build_milk()]))
    renamed = {"slug": "dairy", "name": "Молочні продукти", "sort_order": 3}

    result = load_catalog_file(write_catalog(tmp_path, [], categories=[renamed]))

    category = Category.objects.get(slug="dairy")
    assert result.categories_updated == 1
    assert category.name == "Молочні продукти"
    assert category.sort_order == 3


def test_products_missing_from_the_file_are_kept(tmp_path):
    load_catalog_file(write_catalog(tmp_path, [build_milk()]))

    load_catalog_file(write_catalog(tmp_path, []))

    assert CatalogProduct.objects.filter(name="Молоко 2,5%").exists()


def test_aliases_are_cleaned_up(tmp_path):
    messy = build_milk(aliases=[" молоко ", "молоко", "", "Молоко 2,5%"])

    load_catalog_file(write_catalog(tmp_path, [messy]))

    assert CatalogProduct.objects.get().aliases == ["молоко"]


def test_an_unknown_category_saves_nothing(tmp_path):
    path = write_catalog(tmp_path, [build_milk(category="vegetables")])

    with pytest.raises(CatalogFileError, match="unknown category"):
        load_catalog_file(path)

    assert Category.objects.count() == 0
    assert CatalogProduct.objects.count() == 0


def test_a_product_listed_twice_saves_nothing(tmp_path):
    path = write_catalog(tmp_path, [build_milk(), build_milk(name="молоко 2,5%")])

    with pytest.raises(CatalogFileError, match="listed twice"):
        load_catalog_file(path)

    assert Category.objects.count() == 0
    assert CatalogProduct.objects.count() == 0


def test_invalid_nutrition_saves_nothing(tmp_path):
    path = write_catalog(tmp_path, [build_milk(protein_per_100g=120)])

    with pytest.raises(CatalogFileError, match="protein_per_100g"):
        load_catalog_file(path)

    assert CatalogProduct.objects.count() == 0


def test_a_product_in_pieces_without_grams_is_refused(tmp_path):
    path = write_catalog(tmp_path, [build_milk(default_unit="pcs")])

    with pytest.raises(CatalogFileError, match="grams_per_piece"):
        load_catalog_file(path)


def test_shelf_days_must_be_a_whole_number(tmp_path):
    path = write_catalog(tmp_path, [build_milk(default_shelf_days=7.5)])

    with pytest.raises(CatalogFileError, match="whole number"):
        load_catalog_file(path)


def test_an_entry_with_a_missing_field_is_refused(tmp_path):
    entry = build_milk()
    del entry["default_unit"]

    with pytest.raises(CatalogFileError, match="default_unit"):
        load_catalog_file(write_catalog(tmp_path, [entry]))


def test_a_missing_file_is_refused(tmp_path):
    with pytest.raises(CatalogFileError, match="Cannot read"):
        load_catalog_file(tmp_path / "nothing.json")


def test_a_file_that_is_not_json_is_refused(tmp_path):
    path = tmp_path / "catalog.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(CatalogFileError, match="not valid JSON"):
        load_catalog_file(path)


def test_a_file_without_a_products_list_is_refused(tmp_path):
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps({"categories": []}), encoding="utf-8")

    with pytest.raises(CatalogFileError, match="products"):
        load_catalog_file(path)
