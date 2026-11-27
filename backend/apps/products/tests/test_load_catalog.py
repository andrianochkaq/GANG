import json
from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from apps.products.models import CatalogProduct, Category

pytestmark = pytest.mark.django_db

CATALOG_FIELDS = (
    "id",
    "name",
    "aliases",
    "category__slug",
    "default_unit",
    "kcal_per_100g",
    "protein_per_100g",
    "fat_per_100g",
    "carbs_per_100g",
    "default_shelf_days",
    "grams_per_piece",
)


def take_snapshot():
    category_fields = ("id", "slug", "name", "sort_order")
    categories = Category.objects.order_by("slug").values_list(*category_fields)
    products = CatalogProduct.objects.order_by("name").values_list(*CATALOG_FIELDS)
    return list(categories), list(products)


def run_load_catalog(*args):
    output = StringIO()
    call_command("load_catalog", *args, stdout=output)
    return output.getvalue()


def test_load_catalog_creates_the_bundled_catalog():
    output = run_load_catalog()

    assert Category.objects.count() == 11
    assert CatalogProduct.objects.count() >= 450
    assert f"{CatalogProduct.objects.count()} created" in output


def test_running_load_catalog_twice_gives_the_same_data():
    run_load_catalog()
    first_snapshot = take_snapshot()

    output = run_load_catalog()

    assert take_snapshot() == first_snapshot
    assert "0 created, 0 updated" in output


def test_load_catalog_repairs_a_changed_row():
    run_load_catalog()
    milk = CatalogProduct.objects.get(name="Молоко 2,5%")
    CatalogProduct.objects.filter(pk=milk.pk).update(kcal_per_100g=1)

    output = run_load_catalog()

    milk.refresh_from_db()
    assert milk.kcal_per_100g == 52
    assert "1 updated" in output


def test_load_catalog_reads_the_file_given_with_the_file_option(tmp_path):
    path = tmp_path / "small.json"
    catalog = {
        "categories": [{"slug": "other", "name": "Інше", "sort_order": 0}],
        "products": [],
    }
    path.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")

    run_load_catalog("--file", str(path))

    assert Category.objects.count() == 1
    assert CatalogProduct.objects.count() == 0


def test_load_catalog_reports_a_missing_file_as_a_command_error(tmp_path):
    with pytest.raises(CommandError, match="Cannot read"):
        run_load_catalog("--file", str(tmp_path / "nothing.json"))
