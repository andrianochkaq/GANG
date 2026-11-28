"""Small builders shared by the stock tests."""

from decimal import Decimal

from apps.accounts.models import User
from apps.fridges.models import FridgeMembership, MembershipStatus
from apps.products.models import CatalogProduct, Category, FridgeItem


def make_user(nickname):
    return User.objects.create_user(nickname, email=f"{nickname}@example.com")


def add_member(fridge, user, status=MembershipStatus.ACTIVE):
    return FridgeMembership.objects.create(fridge=fridge, user=user, status=status)


def make_category(slug="dairy", name="Молочне"):
    return Category.objects.create(slug=slug, name=name)


def make_catalog_product(category, name="Молоко 2,5%", unit="ml", **extra):
    return CatalogProduct.objects.create(
        name=name,
        category=category,
        default_unit=unit,
        kcal_per_100g=Decimal("52"),
        protein_per_100g=Decimal("2.9"),
        fat_per_100g=Decimal("2.5"),
        carbs_per_100g=Decimal("4.8"),
        default_shelf_days=7,
        **extra,
    )


def make_item(fridge, category, name="Молоко", quantity="500", unit="ml", **extra):
    return FridgeItem.objects.create(
        fridge=fridge,
        category=category,
        name=name,
        quantity=Decimal(quantity),
        unit=unit,
        **extra,
    )
