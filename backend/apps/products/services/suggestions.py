"""Product suggestions for the add-product input.

While a person types, the client asks for up to eight names. They come
from these places, in this order:

1. items already in this fridge: names that start with the text, then
   similar names (most people add what they bought before);
2. catalog products whose name starts with the text;
3. catalog products with an alias that starts with the text;
4. catalog products with a similar name, to forgive typos.

A name is offered once: a catalog product that the fridge already has
(same catalog link or same name) is left out. Similar names are found
with ``pg_trgm`` (``SIMILARITY``); prefixes ignore case.
"""

from dataclasses import dataclass
from uuid import UUID

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import BooleanField, Q, TextChoices
from django.db.models.expressions import RawSQL
from django.db.models.functions import Length

from apps.products.models import CatalogProduct, FridgeItem

MAX_SUGGESTIONS = 8

# The default threshold of pg_trgm: "молко" is close to "молоко",
# "мо" is only a prefix of it.
MIN_SIMILARITY = 0.3

# One name can sit in a fridge many times (other expiry dates). Look at
# this many rows before the repeats are merged.
MAX_FRIDGE_ROWS = 100

# Aliases are a JSON list on the product. The CASE keeps
# jsonb_array_elements_text away from a value that is not a list.
ALIAS_STARTS_WITH_SQL = """
    CASE
        WHEN jsonb_typeof("products_catalogproduct"."aliases") = 'array' THEN
            EXISTS (
                SELECT 1
                FROM jsonb_array_elements_text("products_catalogproduct"."aliases")
                    AS alias_item(alias_text)
                WHERE alias_item.alias_text ILIKE %s
            )
        ELSE FALSE
    END
"""


class SuggestionSource(TextChoices):
    """Where a suggested name comes from."""

    FRIDGE = "fridge", "У холодильнику"
    CATALOG = "catalog", "З каталогу"


@dataclass(frozen=True)
class ProductSuggestion:
    """A name to offer, with what is needed to add it with one tap."""

    source: str
    name: str
    unit: str
    category: str
    catalog_product: UUID | None


def suggest_products(fridge_id, text, limit=MAX_SUGGESTIONS):
    """Return up to ``limit`` suggestions for what the person has typed."""
    text = text.strip()
    if not text:
        return []
    suggestions = _find_fridge_suggestions(fridge_id, text, limit)
    known_names = {suggestion.name.lower() for suggestion in suggestions}
    known_products = {
        suggestion.catalog_product
        for suggestion in suggestions
        if suggestion.catalog_product is not None
    }
    # Catalog rows that repeat a fridge suggestion are skipped, so ask for
    # that many more.
    row_limit = limit + len(suggestions)
    for tier in _build_catalog_tiers(text):
        if len(suggestions) >= limit:
            break
        for row in tier[:row_limit]:
            name_key = row["name"].lower()
            if row["id"] in known_products or name_key in known_names:
                continue
            suggestions.append(_build_catalog_suggestion(row))
            known_names.add(name_key)
            if len(suggestions) >= limit:
                break
    return suggestions


def _find_fridge_suggestions(fridge_id, text, limit):
    items = FridgeItem.objects.filter(fridge_id=fridge_id)
    name_starts = Q(name__istartswith=text)
    tiers = (
        items.filter(name_starts).order_by(Length("name"), "name"),
        _keep_similar(items.exclude(name_starts), text),
    )
    suggestions = []
    seen = set()
    for tier in tiers:
        if len(suggestions) >= limit:
            break
        rows = tier.values("name", "unit", "category__slug", "catalog_product_id")
        for row in rows[:MAX_FRIDGE_ROWS]:
            key = (row["name"].lower(), row["unit"])
            if key not in seen:
                seen.add(key)
                suggestions.append(_build_fridge_suggestion(row))
    return suggestions[:limit]


def _build_catalog_tiers(text):
    """Return the catalog queries, best matches first; none runs until read."""
    catalog = CatalogProduct.objects.annotate(matches_alias=_build_alias_match(text))
    name_starts = Q(name__istartswith=text)
    alias_starts = Q(matches_alias=True)
    by_length = (Length("name"), "name")
    fields = ("id", "name", "default_unit", "category__slug")
    by_name = catalog.filter(name_starts).order_by(*by_length)
    by_alias = catalog.filter(alias_starts).exclude(name_starts).order_by(*by_length)
    similar = _keep_similar(catalog.exclude(name_starts | alias_starts), text)
    return (
        by_name.values(*fields),
        by_alias.values(*fields),
        similar.values(*fields),
    )


def _build_alias_match(text):
    pattern = _escape_like(text) + "%"
    return RawSQL(ALIAS_STARTS_WITH_SQL, [pattern], output_field=BooleanField())


def _escape_like(text):
    """Make ``%``, ``_`` and the backslash plain characters in a LIKE pattern."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _keep_similar(queryset, text):
    """Keep the names that resemble the text, the closest first."""
    similar = queryset.annotate(similarity=TrigramSimilarity("name", text))
    similar = similar.filter(similarity__gte=MIN_SIMILARITY)
    return similar.order_by("-similarity", "name")


def _build_fridge_suggestion(row):
    return ProductSuggestion(
        source=SuggestionSource.FRIDGE,
        name=row["name"],
        unit=row["unit"],
        category=row["category__slug"],
        catalog_product=row["catalog_product_id"],
    )


def _build_catalog_suggestion(row):
    return ProductSuggestion(
        source=SuggestionSource.CATALOG,
        name=row["name"],
        unit=row["default_unit"],
        category=row["category__slug"],
        catalog_product=row["id"],
    )
