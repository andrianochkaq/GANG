"""Loads the product catalog from a JSON file into the database.

The file lists categories (matched by ``slug``) and products (matched by
``name``). Loading is idempotent: a second run with the same file changes
nothing. Products that are not in the file are left alone, because fridge
items may already point to them.

File shape::

    {"categories": [{"slug": "dairy", "name": "Молочне", "sort_order": 0}],
     "products": [{"name": "Молоко 2,5%", "aliases": ["молоко"],
                   "category": "dairy", "default_unit": "ml", ...}]}
"""

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.products.models import CatalogProduct, Category

DEFAULT_CATALOG_PATH = (
    Path(__file__).resolve().parent.parent / "fixtures" / "catalog_uk.json"
)

_CATEGORY_FIELDS = ("slug", "name", "sort_order")
_PRODUCT_FIELDS = (
    "name",
    "aliases",
    "category",
    "default_unit",
    "kcal_per_100g",
    "protein_per_100g",
    "fat_per_100g",
    "carbs_per_100g",
    "default_shelf_days",
    "grams_per_piece",
)


class CatalogFileError(Exception):
    """The catalog file is missing, unreadable or has invalid content."""


@dataclass
class CatalogLoadResult:
    """How many rows a load created, changed or left as they were."""

    categories_created: int = 0
    categories_updated: int = 0
    products_created: int = 0
    products_updated: int = 0
    products_unchanged: int = 0


def load_catalog_file(path=DEFAULT_CATALOG_PATH):
    """Create or update categories and products from the file at ``path``.

    Everything happens in one transaction: if any entry is invalid,
    nothing is saved and ``CatalogFileError`` is raised.
    """
    data = _read_catalog_file(Path(path))
    category_entries = _get_entries(data, "categories")
    product_entries = _get_entries(data, "products")
    result = CatalogLoadResult()
    with transaction.atomic():
        categories_by_slug = _sync_categories(category_entries, result)
        _sync_products(product_entries, categories_by_slug, result)
    return result


def _read_catalog_file(path):
    try:
        with path.open(encoding="utf-8") as catalog_file:
            data = json.load(catalog_file, parse_float=Decimal)
    except OSError as error:
        raise CatalogFileError(f"Cannot read {path}: {error.strerror}") from error
    except ValueError as error:
        raise CatalogFileError(f"{path} is not valid JSON: {error}") from error
    if not isinstance(data, dict):
        raise CatalogFileError("The catalog file must hold a JSON object.")
    return data


def _get_entries(data, key):
    entries = data.get(key)
    if not isinstance(entries, list):
        raise CatalogFileError(f'The catalog file needs a "{key}" list.')
    return entries


def _read_entry(entry, field_names, label):
    """Return a copy of a file entry after checking it has every field."""
    if not isinstance(entry, dict):
        raise CatalogFileError(f"Every {label} entry must be a JSON object.")
    missing = [name for name in field_names if name not in entry]
    if missing:
        raise CatalogFileError(
            f"A {label} entry is missing {', '.join(missing)}: {entry}"
        )
    return dict(entry)


def _sync_categories(entries, result):
    existing = {category.slug: category for category in Category.objects.all()}
    categories_by_slug = {}
    for entry in entries:
        values = _read_entry(entry, _CATEGORY_FIELDS, "category")
        slug = values.pop("slug")
        category = existing.get(slug)
        if category is None:
            category = Category(slug=slug, **values)
            _save_valid(category)
            result.categories_created += 1
        elif _apply_values(category, values):
            _save_valid(category)
            result.categories_updated += 1
        categories_by_slug[slug] = category
    return categories_by_slug


def _sync_products(entries, categories_by_slug, result):
    existing = {product.name: product for product in CatalogProduct.objects.all()}
    seen_names = set()
    for entry in entries:
        values = _read_product_values(entry, categories_by_slug)
        name = values.pop("name")
        if name.casefold() in seen_names:
            raise CatalogFileError(f"The product {name} is listed twice.")
        seen_names.add(name.casefold())
        product = existing.get(name)
        if product is None:
            product = CatalogProduct(name=name, **values)
            _save_valid(product)
            result.products_created += 1
        elif _apply_values(product, values):
            _save_valid(product)
            result.products_updated += 1
        else:
            result.products_unchanged += 1


def _read_product_values(entry, categories_by_slug):
    values = _read_entry(entry, _PRODUCT_FIELDS, "product")
    name = values["name"]
    if not isinstance(name, str) or not name.strip():
        raise CatalogFileError(f"A product needs a name: {entry}")
    values["name"] = name.strip()
    values["aliases"] = _normalize_aliases(values["aliases"], values["name"])
    category = categories_by_slug.get(values.pop("category"))
    if category is None:
        raise CatalogFileError(f"The product {name} has an unknown category.")
    values["category_id"] = category.pk
    for field_name in ("default_shelf_days", "grams_per_piece"):
        _check_whole_number(values[field_name], field_name, name)
    return values


def _normalize_aliases(aliases, name):
    """Strip aliases and drop empty ones, repeats and the name itself."""
    if not isinstance(aliases, list):
        raise CatalogFileError(f"The aliases of {name} must be a list.")
    normalized = []
    for alias in aliases:
        if isinstance(alias, str):
            alias = alias.strip()
            if alias and alias != name and alias not in normalized:
                normalized.append(alias)
        else:
            raise CatalogFileError(f"The aliases of {name} must be strings.")
    return normalized


def _check_whole_number(value, field_name, name):
    if value is None and field_name == "grams_per_piece":
        return
    if not isinstance(value, int) or isinstance(value, bool):
        raise CatalogFileError(f"{field_name} of {name} must be a whole number.")


def _apply_values(instance, values):
    """Set the values that differ on the instance; tell if any did."""
    has_changes = False
    for field_name, value in values.items():
        if getattr(instance, field_name) != value:
            setattr(instance, field_name, value)
            has_changes = True
    return has_changes


def _save_valid(instance):
    try:
        instance.full_clean()
    except ValidationError as error:
        label = getattr(instance, "name", instance)
        raise CatalogFileError(
            f"{label} is invalid: {_describe_errors(error)}"
        ) from error
    instance.save()


def _describe_errors(error):
    return "; ".join(
        f"{field_name}: {' '.join(messages)}"
        for field_name, messages in error.message_dict.items()
    )
