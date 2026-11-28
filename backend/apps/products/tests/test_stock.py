import datetime
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction

from apps.fridges.models import Fridge
from apps.fridges.services import annotate_fridge_summary, create_fridge
from apps.products.models import FridgeItem, StockMovement, StockReason
from apps.products.services.stock import (
    CategoryRequiredError,
    ItemNotFoundError,
    QuantityBelowZeroError,
    add_item,
    add_items,
    consume_item,
    delete_item,
    filter_items,
    update_item,
)
from apps.products.tests.factories import (
    make_catalog_product,
    make_category,
    make_item,
    make_user,
)

pytestmark = pytest.mark.django_db

EXPIRY_DATE = datetime.date(2026, 12, 1)


@pytest.fixture
def user():
    return make_user("anna")


@pytest.fixture
def fridge(user):
    return create_fridge(user, "Дача")


@pytest.fixture
def dairy():
    return make_category("dairy", "Молочне")


@pytest.fixture
def other():
    return make_category("other", "Інше")


def add_milk(fridge, user, dairy, quantity="500", **extra):
    arguments = {
        "name": "Молоко",
        "quantity": Decimal(quantity),
        "unit": "ml",
        "category": dairy,
    }
    arguments.update(extra)
    return add_item(fridge, user, **arguments)


def latest_movement():
    return StockMovement.objects.order_by("-at", "-id").first()


# --- adding ---


def test_add_item_creates_an_item_and_one_movement(fridge, user, dairy):
    added = add_milk(fridge, user, dairy, expires_at=EXPIRY_DATE)

    assert added.is_new is True
    assert added.item.quantity == Decimal("500")
    assert added.item.added_by == user
    assert added.item.expires_at == EXPIRY_DATE
    movement = StockMovement.objects.get()
    assert movement.item == added.item
    assert movement.fridge == fridge
    assert movement.delta == Decimal("500")
    assert movement.quantity_after == Decimal("500")
    assert movement.reason == StockReason.MANUAL
    assert movement.user == user
    assert movement.item_name == "Молоко"
    assert movement.unit == "ml"


def test_add_item_records_the_reason(fridge, user, dairy):
    add_milk(fridge, user, dairy, reason=StockReason.RECEIPT)

    assert StockMovement.objects.get().reason == StockReason.RECEIPT


def test_adding_the_same_product_raises_the_quantity(fridge, user, dairy):
    first = add_milk(fridge, user, dairy, quantity="500", expires_at=EXPIRY_DATE)

    second = add_milk(fridge, user, dairy, quantity="250", expires_at=EXPIRY_DATE)

    assert second.is_new is False
    assert second.item.pk == first.item.pk
    assert FridgeItem.objects.count() == 1
    assert FridgeItem.objects.get().quantity == Decimal("750")
    assert StockMovement.objects.count() == 2
    assert latest_movement().delta == Decimal("250")
    assert latest_movement().quantity_after == Decimal("750")


def test_the_name_is_matched_ignoring_case(fridge, user, dairy):
    add_milk(fridge, user, dairy, name="Молоко")

    added = add_milk(fridge, user, dairy, name="молоко")

    assert added.is_new is False
    assert FridgeItem.objects.count() == 1


def test_a_different_unit_makes_a_separate_item(fridge, user, dairy):
    add_milk(fridge, user, dairy, unit="ml")

    added = add_milk(fridge, user, dairy, unit="l")

    assert added.is_new is True
    assert FridgeItem.objects.count() == 2


def test_a_different_expiry_makes_a_separate_item(fridge, user, dairy):
    add_milk(fridge, user, dairy, expires_at=EXPIRY_DATE)

    added = add_milk(fridge, user, dairy, expires_at=None)

    assert added.is_new is True
    assert FridgeItem.objects.count() == 2


def test_items_without_expiry_merge(fridge, user, dairy):
    add_milk(fridge, user, dairy)

    added = add_milk(fridge, user, dairy)

    assert added.is_new is False
    assert FridgeItem.objects.get().quantity == Decimal("1000")


def test_the_same_product_in_another_fridge_is_separate(fridge, user, dairy):
    other_fridge = create_fridge(user, "Квартира")
    add_milk(fridge, user, dairy)

    added = add_milk(other_fridge, user, dairy)

    assert added.is_new is True
    assert FridgeItem.objects.count() == 2


def test_catalog_products_merge_by_product_not_by_name(fridge, user, dairy):
    milk = make_catalog_product(dairy)
    first = add_milk(fridge, user, dairy, name="Молоко", catalog_product=milk)

    second = add_milk(fridge, user, dairy, name="Молочко", catalog_product=milk)

    assert second.is_new is False
    assert second.item.pk == first.item.pk


def test_a_catalog_product_does_not_merge_into_a_plain_item(fridge, user, dairy):
    add_milk(fridge, user, dairy, name="Молоко")

    added = add_milk(
        fridge,
        user,
        dairy,
        name="Молоко",
        catalog_product=make_catalog_product(dairy),
    )

    assert added.is_new is True


def test_the_category_of_the_catalog_product_is_used(fridge, user, dairy, other):
    milk = make_catalog_product(dairy)

    added = add_item(
        fridge,
        user,
        name="Молоко",
        quantity=Decimal("1"),
        unit="l",
        catalog_product=milk,
    )

    assert added.item.category == dairy


def test_a_given_category_wins_over_the_catalog_product(fridge, user, dairy, other):
    milk = make_catalog_product(dairy)

    added = add_milk(fridge, user, other, catalog_product=milk)

    assert added.item.category == other


def test_without_a_category_the_item_goes_to_other(fridge, user, other):
    added = add_item(fridge, user, name="Щось", quantity=Decimal("1"), unit="pcs")

    assert added.item.category == other


def test_without_a_category_and_without_other_nothing_is_added(fridge, user):
    with pytest.raises(CategoryRequiredError):
        add_item(fridge, user, name="Щось", quantity=Decimal("1"), unit="pcs")

    assert FridgeItem.objects.count() == 0
    assert StockMovement.objects.count() == 0


# --- adding several ---


def build_line(dairy, name="Молоко", quantity="1", unit="l"):
    return {
        "name": name,
        "quantity": Decimal(quantity),
        "unit": unit,
        "category": dairy,
    }


def test_add_items_adds_every_line_with_one_movement_each(fridge, user, dairy):
    lines = [build_line(dairy), build_line(dairy, "Сир", "200", "g")]

    added = add_items(fridge, user, lines, reason=StockReason.RECEIPT)

    assert [entry.item.name for entry in added] == ["Молоко", "Сир"]
    assert all(entry.is_new for entry in added)
    assert StockMovement.objects.filter(reason=StockReason.RECEIPT).count() == 2


def test_add_items_merges_lines_of_the_same_product(fridge, user, dairy):
    lines = [build_line(dairy), build_line(dairy)]

    added = add_items(fridge, user, lines)

    assert [entry.is_new for entry in added] == [True, False]
    assert added[0].item.pk == added[1].item.pk
    assert added[0].item.quantity == Decimal("2")
    assert FridgeItem.objects.get().quantity == Decimal("2")
    assert StockMovement.objects.count() == 2


def test_add_items_adds_nothing_when_one_line_fails(fridge, user, dairy):
    lines = [
        build_line(dairy),
        {"name": "Щось", "quantity": Decimal("1"), "unit": "pcs"},
    ]

    with pytest.raises(CategoryRequiredError):
        add_items(fridge, user, lines)

    assert FridgeItem.objects.count() == 0
    assert StockMovement.objects.count() == 0


# --- changing ---


def test_update_item_with_a_new_quantity_writes_one_movement(fridge, user, dairy):
    item = add_milk(fridge, user, dairy, quantity="500").item

    updated = update_item(item, user, quantity=Decimal("300"))

    assert updated.quantity == Decimal("300")
    assert StockMovement.objects.count() == 2
    assert latest_movement().delta == Decimal("-200")
    assert latest_movement().quantity_after == Decimal("300")


def test_update_item_can_raise_the_quantity_with_a_reason(fridge, user, dairy):
    item = add_milk(fridge, user, dairy, quantity="500").item

    update_item(item, user, quantity=Decimal("800"), reason=StockReason.CALORIES)

    movement = StockMovement.objects.get(reason=StockReason.CALORIES)
    assert movement.delta == Decimal("300")


def test_update_item_without_a_quantity_change_writes_no_movement(fridge, user, dairy):
    item = add_milk(fridge, user, dairy, quantity="500").item

    updated = update_item(item, user, name="Молоко домашнє", expires_at=EXPIRY_DATE)

    assert updated.name == "Молоко домашнє"
    assert updated.expires_at == EXPIRY_DATE
    assert StockMovement.objects.count() == 1


def test_update_item_with_the_same_quantity_writes_no_movement(fridge, user, dairy):
    item = add_milk(fridge, user, dairy, quantity="500").item

    update_item(item, user, quantity=Decimal("500"))

    assert StockMovement.objects.count() == 1


def test_update_item_of_a_removed_item_is_refused(fridge, user, dairy):
    item = add_milk(fridge, user, dairy).item
    FridgeItem.objects.filter(pk=item.pk).delete()

    with pytest.raises(ItemNotFoundError):
        update_item(item, user, name="Молоко")


# --- consuming ---


def test_consume_item_takes_an_amount_and_writes_one_movement(fridge, user, dairy):
    item = add_milk(fridge, user, dairy, quantity="500").item

    remaining = consume_item(item, user, Decimal("200"), reason=StockReason.RECIPE)

    assert remaining.quantity == Decimal("300")
    assert FridgeItem.objects.get().quantity == Decimal("300")
    movement = StockMovement.objects.get(reason=StockReason.RECIPE)
    assert movement.delta == Decimal("-200")
    assert movement.quantity_after == Decimal("300")
    assert movement.item == item


def test_consuming_everything_removes_the_item_but_keeps_the_history(
    fridge, user, dairy
):
    item = add_milk(fridge, user, dairy, quantity="500").item

    remaining = consume_item(item, user, Decimal("500"))

    assert remaining is None
    assert FridgeItem.objects.count() == 0
    assert StockMovement.objects.count() == 2
    movement = latest_movement()
    assert movement.delta == Decimal("-500")
    assert movement.quantity_after == Decimal("0")
    assert movement.item is None
    assert movement.item_name == "Молоко"


def test_consuming_more_than_there_is_changes_nothing(fridge, user, dairy):
    item = add_milk(fridge, user, dairy, quantity="500").item

    with pytest.raises(QuantityBelowZeroError) as error:
        consume_item(item, user, Decimal("500.001"))

    assert error.value.available == Decimal("500")
    assert FridgeItem.objects.get().quantity == Decimal("500")
    assert StockMovement.objects.count() == 1


def test_consume_item_of_a_removed_item_is_refused(fridge, user, dairy):
    item = add_milk(fridge, user, dairy).item
    FridgeItem.objects.filter(pk=item.pk).delete()

    with pytest.raises(ItemNotFoundError):
        consume_item(item, user, Decimal("1"))


# --- removing ---


def test_delete_item_removes_it_and_records_what_was_left(fridge, user, dairy):
    item = add_milk(fridge, user, dairy, quantity="500").item

    delete_item(item, user)

    assert FridgeItem.objects.count() == 0
    movement = latest_movement()
    assert movement.delta == Decimal("-500")
    assert movement.quantity_after == Decimal("0")
    assert movement.reason == StockReason.MANUAL
    assert movement.item is None


# --- filters ---


def test_filter_items_by_category_and_search(fridge, dairy, other):
    make_item(fridge, dairy, name="Молоко")
    make_item(fridge, dairy, name="Кефір")
    make_item(fridge, other, name="Молочний шоколад", unit="g")
    items = FridgeItem.objects.all()

    by_category = filter_items(items, category_slug="dairy")
    by_search = filter_items(items, search="Молоч")
    by_both = filter_items(items, category_slug="other", search="Молоч")

    assert sorted(item.name for item in by_category) == ["Кефір", "Молоко"]
    assert [item.name for item in by_search] == ["Молочний шоколад"]
    assert [item.name for item in by_both] == ["Молочний шоколад"]


def test_filter_items_ignores_empty_values(fridge, dairy):
    make_item(fridge, dairy, name="Молоко")

    items = filter_items(FridgeItem.objects.all(), category_slug="", search="  ")

    assert items.count() == 1


# --- database rules ---


@pytest.mark.parametrize("quantity", ["0", "-1"])
def test_the_database_refuses_a_quantity_of_zero_or_less(fridge, dairy, quantity):
    with pytest.raises(IntegrityError), transaction.atomic():
        make_item(fridge, dairy, quantity=quantity)


def test_the_database_refuses_a_negative_quantity_in_the_history(fridge):
    with pytest.raises(IntegrityError), transaction.atomic():
        StockMovement.objects.create(
            fridge=fridge,
            item_name="Молоко",
            unit="ml",
            delta=Decimal("-1"),
            quantity_after=Decimal("-1"),
            reason=StockReason.MANUAL,
        )


def test_deleting_a_fridge_deletes_its_items_and_history(fridge, user, dairy):
    add_milk(fridge, user, dairy)

    fridge.delete()

    assert FridgeItem.objects.count() == 0
    assert StockMovement.objects.count() == 0


# --- the fridge summary ---


def test_the_fridge_summary_counts_items(fridge, user, dairy):
    make_item(fridge, dairy, name="Молоко")
    make_item(fridge, dairy, name="Кефір")
    other_fridge = create_fridge(user, "Квартира")
    make_item(other_fridge, dairy, name="Сир", unit="g")

    summary = annotate_fridge_summary(Fridge.objects.filter(pk=fridge.pk)).get()

    assert summary.product_count == 2
