import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.fridges.models import MembershipStatus
from apps.fridges.services import create_fridge
from apps.products.models import FridgeItem, StockMovement, StockReason
from apps.products.tests.factories import (
    add_member,
    make_catalog_product,
    make_category,
    make_item,
    make_user,
)
from apps.products.views import flatten_error_details

pytestmark = pytest.mark.django_db


def items_url(fridge):
    return f"/api/fridges/{fridge.pk}/items/"


def item_url(fridge, item):
    return f"{items_url(fridge)}{item.pk}/"


def consume_url(fridge, item):
    return f"{item_url(fridge, item)}consume/"


def bulk_url(fridge):
    return f"{items_url(fridge)}bulk/"


def client_for(user):
    api_client = APIClient()
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def owner():
    return make_user("anna")


@pytest.fixture
def fridge(owner):
    return create_fridge(owner, "Дача")


@pytest.fixture
def member(fridge):
    member = make_user("olga")
    add_member(fridge, member)
    return member


@pytest.fixture
def stranger():
    return make_user("petro")


@pytest.fixture
def dairy():
    return make_category("dairy", "Молочне")


@pytest.fixture
def other():
    return make_category("other", "Інше")


@pytest.fixture
def milk(fridge, dairy):
    return make_item(fridge, dairy, name="Молоко", quantity="500", unit="ml")


def post_item(user, fridge, **payload):
    return client_for(user).post(items_url(fridge), payload, format="json")


def quantity_of(response):
    return Decimal(response.json()["quantity"])


# --- who can reach the items ---


def test_list_requires_a_login(fridge):
    response = APIClient().get(items_url(fridge))

    assert response.status_code == 401


def test_a_stranger_gets_404_everywhere(fridge, stranger, milk):
    api_client = client_for(stranger)

    responses = [
        api_client.get(items_url(fridge)),
        api_client.get(item_url(fridge, milk)),
        api_client.post(items_url(fridge), {}, format="json"),
        api_client.post(bulk_url(fridge), {}, format="json"),
        api_client.patch(item_url(fridge, milk), {}, format="json"),
        api_client.delete(item_url(fridge, milk)),
        api_client.post(consume_url(fridge, milk), {}, format="json"),
    ]

    assert [response.status_code for response in responses] == [404] * 7
    assert FridgeItem.objects.get() == milk


def test_a_member_whose_request_is_pending_gets_404(fridge, milk):
    applicant = make_user("ivan")
    add_member(fridge, applicant, status=MembershipStatus.PENDING)

    response = client_for(applicant).get(items_url(fridge))

    assert response.status_code == 404


def test_a_member_can_use_the_items(fridge, member, milk):
    response = client_for(member).get(items_url(fridge))

    assert response.status_code == 200
    assert [item["name"] for item in response.json()["results"]] == ["Молоко"]


# --- the list ---


def test_list_shows_the_fields_of_an_item(fridge, owner, milk):
    response = client_for(owner).get(items_url(fridge))

    item = response.json()["results"][0]
    assert set(item) == {
        "id",
        "name",
        "catalog_product",
        "category",
        "quantity",
        "unit",
        "expires_at",
        "opened_at",
        "added_by",
        "created_at",
    }
    assert item["id"] == str(milk.pk)
    assert item["category"] == "dairy"
    assert item["unit"] == "ml"
    assert Decimal(item["quantity"]) == Decimal("500")
    assert item["catalog_product"] is None
    assert item["expires_at"] is None


def test_list_shows_only_the_items_of_this_fridge(fridge, owner, dairy, milk):
    other_fridge = create_fridge(owner, "Квартира")
    make_item(other_fridge, dairy, name="Кефір")

    response = client_for(owner).get(items_url(fridge))

    assert [item["name"] for item in response.json()["results"]] == ["Молоко"]


def test_list_is_ordered_by_name(fridge, owner, dairy):
    for name in ("Сир", "Кефір", "Масло"):
        make_item(fridge, dairy, name=name, unit="g")

    response = client_for(owner).get(items_url(fridge))

    names = [item["name"] for item in response.json()["results"]]
    assert names == ["Кефір", "Масло", "Сир"]


def test_list_can_be_filtered_by_category(fridge, owner, dairy, other):
    make_item(fridge, dairy, name="Молоко")
    make_item(fridge, other, name="Сіль", unit="g")

    response = client_for(owner).get(items_url(fridge), {"category": "other"})

    assert [item["name"] for item in response.json()["results"]] == ["Сіль"]


def test_list_can_be_searched_by_name(fridge, owner, dairy):
    make_item(fridge, dairy, name="Молоко")
    make_item(fridge, dairy, name="Кефір")

    response = client_for(owner).get(items_url(fridge), {"search": "Кеф"})

    assert [item["name"] for item in response.json()["results"]] == ["Кефір"]


def test_list_is_paged_with_a_cursor(fridge, owner, dairy):
    for name in ("Кефір", "Масло", "Сир"):
        make_item(fridge, dairy, name=name, unit="g")
    api_client = client_for(owner)

    first_page = api_client.get(items_url(fridge), {"page_size": 2}).json()
    second_page = api_client.get(first_page["next"]).json()

    assert [item["name"] for item in first_page["results"]] == ["Кефір", "Масло"]
    assert [item["name"] for item in second_page["results"]] == ["Сир"]
    assert second_page["next"] is None


# --- adding ---


def test_create_adds_an_item_and_records_it(fridge, owner, dairy):
    response = post_item(
        owner,
        fridge,
        name="Молоко",
        quantity="500",
        unit="ml",
        category="dairy",
        expires_at="2026-12-05",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Молоко"
    assert body["category"] == "dairy"
    assert body["expires_at"] == "2026-12-05"
    assert body["added_by"] == str(owner.pk)
    assert Decimal(body["quantity"]) == Decimal("500")
    movement = StockMovement.objects.get()
    assert movement.delta == Decimal("500")
    assert movement.reason == StockReason.MANUAL
    assert movement.user == owner


def test_create_with_a_catalog_product_fills_the_rest(fridge, owner, dairy):
    product = make_catalog_product(dairy, name="Молоко 2,5%", unit="ml")

    response = post_item(owner, fridge, catalog_product=str(product.pk), quantity="1")

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Молоко 2,5%"
    assert body["unit"] == "ml"
    assert body["category"] == "dairy"
    assert body["catalog_product"] == str(product.pk)


def test_create_without_a_category_puts_the_item_into_other(fridge, owner, other):
    response = post_item(owner, fridge, name="Щось", quantity="2", unit="pcs")

    assert response.status_code == 201
    assert response.json()["category"] == "other"


def test_create_raises_an_item_that_is_already_there(fridge, owner, dairy, milk):
    response = post_item(
        owner, fridge, name="Молоко", quantity="250", unit="ml", category="dairy"
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(milk.pk)
    assert quantity_of(response) == Decimal("750")
    assert FridgeItem.objects.count() == 1
    assert StockMovement.objects.get().delta == Decimal("250")


def test_create_keeps_the_reason(fridge, owner, dairy):
    post_item(
        owner,
        fridge,
        name="Молоко",
        quantity="1",
        unit="l",
        category="dairy",
        reason="calories",
    )

    assert StockMovement.objects.get().reason == StockReason.CALORIES


@pytest.mark.parametrize(
    "payload, field_name",
    [
        ({"quantity": "1", "unit": "g"}, "name"),
        ({"name": "Молоко", "quantity": "1"}, "unit"),
        ({"name": "Молоко", "unit": "g"}, "quantity"),
        ({"name": "Молоко", "unit": "g", "quantity": "0"}, "quantity"),
        ({"name": "Молоко", "unit": "g", "quantity": "-5"}, "quantity"),
        ({"name": "Молоко", "unit": "g", "quantity": "abc"}, "quantity"),
        ({"name": "Молоко", "unit": "oz", "quantity": "1"}, "unit"),
        ({"name": "Молоко", "unit": "g", "quantity": "1", "category": "x"}, "category"),
        ({"name": "Молоко", "unit": "g", "quantity": "1", "reason": "x"}, "reason"),
        ({"name": "", "unit": "g", "quantity": "1"}, "name"),
        (
            {"name": "Молоко", "unit": "g", "quantity": "1", "expires_at": "завтра"},
            "expires_at",
        ),
        (
            {"unit": "g", "quantity": "1", "catalog_product": str(uuid.uuid4())},
            "catalog_product",
        ),
    ],
)
def test_create_refuses_bad_data(fridge, owner, dairy, payload, field_name):
    response = post_item(owner, fridge, **payload)

    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "validation_error"
    assert field_name in body["fields"]
    assert FridgeItem.objects.count() == 0
    assert StockMovement.objects.count() == 0


def test_create_without_any_category_to_use_is_refused(fridge, owner):
    response = post_item(owner, fridge, name="Щось", quantity="1", unit="pcs")

    assert response.status_code == 400
    assert response.json()["code"] == "category_required"
    assert FridgeItem.objects.count() == 0


# --- adding several ---


def test_bulk_adds_every_line_and_records_the_reason(fridge, owner, dairy):
    payload = {
        "reason": "receipt",
        "items": [
            {"name": "Молоко", "quantity": "1", "unit": "l", "category": "dairy"},
            {"name": "Сир", "quantity": "200", "unit": "g", "category": "dairy"},
        ],
    }

    response = client_for(owner).post(bulk_url(fridge), payload, format="json")

    assert response.status_code == 201
    names = [item["name"] for item in response.json()["items"]]
    assert names == ["Молоко", "Сир"]
    assert FridgeItem.objects.count() == 2
    assert StockMovement.objects.filter(reason=StockReason.RECEIPT).count() == 2


def test_bulk_merges_lines_and_shows_the_final_quantity(fridge, owner, dairy, milk):
    line = {"name": "Молоко", "quantity": "100", "unit": "ml", "category": "dairy"}

    response = client_for(owner).post(
        bulk_url(fridge), {"items": [line, line]}, format="json"
    )

    assert response.status_code == 201
    quantities = [Decimal(item["quantity"]) for item in response.json()["items"]]
    assert quantities == [Decimal("700"), Decimal("700")]
    assert FridgeItem.objects.get().quantity == Decimal("700")


def test_bulk_adds_nothing_when_a_line_is_wrong(fridge, owner, dairy):
    payload = {
        "items": [
            {"name": "Молоко", "quantity": "1", "unit": "l", "category": "dairy"},
            {"name": "Сир", "quantity": "0", "unit": "g", "category": "dairy"},
        ],
    }

    response = client_for(owner).post(bulk_url(fridge), payload, format="json")

    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "validation_error"
    assert list(body["fields"]) == ["items.1.quantity"]
    assert FridgeItem.objects.count() == 0


def test_bulk_adds_nothing_when_a_category_cannot_be_found(fridge, owner, dairy):
    payload = {
        "items": [
            {"name": "Молоко", "quantity": "1", "unit": "l", "category": "dairy"},
            {"name": "Щось", "quantity": "1", "unit": "pcs"},
        ],
    }

    response = client_for(owner).post(bulk_url(fridge), payload, format="json")

    assert response.status_code == 400
    assert response.json()["code"] == "category_required"
    assert FridgeItem.objects.count() == 0
    assert StockMovement.objects.count() == 0


def test_bulk_refuses_an_empty_list(fridge, owner):
    response = client_for(owner).post(bulk_url(fridge), {"items": []}, format="json")

    assert response.status_code == 400
    assert "items" in response.json()["fields"]


def test_bulk_refuses_too_many_lines(fridge, owner, dairy):
    line = {"name": "Сіль", "quantity": "1", "unit": "g", "category": "dairy"}

    response = client_for(owner).post(
        bulk_url(fridge), {"items": [line] * 101}, format="json"
    )

    assert response.status_code == 400
    assert "items" in response.json()["fields"]
    assert FridgeItem.objects.count() == 0


def test_bulk_refuses_a_reason_it_does_not_know(fridge, owner, dairy):
    line = {"name": "Сіль", "quantity": "1", "unit": "g", "category": "dairy"}

    response = client_for(owner).post(
        bulk_url(fridge), {"reason": "x", "items": [line]}, format="json"
    )

    assert response.status_code == 400
    assert "reason" in response.json()["fields"]


# --- one item ---


def test_retrieve_shows_the_item(fridge, owner, milk):
    response = client_for(owner).get(item_url(fridge, milk))

    assert response.status_code == 200
    assert response.json()["name"] == "Молоко"


def test_an_item_of_another_fridge_is_not_found(fridge, owner, stranger, dairy):
    other_fridge = create_fridge(stranger, "Чужий")
    foreign_item = make_item(other_fridge, dairy, name="Кефір")
    api_client = client_for(owner)

    assert api_client.get(item_url(fridge, foreign_item)).status_code == 404
    assert api_client.delete(item_url(fridge, foreign_item)).status_code == 404
    assert FridgeItem.objects.filter(pk=foreign_item.pk).exists()


def test_an_unknown_item_is_not_found(fridge, owner):
    response = client_for(owner).get(f"{items_url(fridge)}{uuid.uuid4()}/")

    assert response.status_code == 404


# --- changing ---


def test_patch_changes_fields_without_a_movement(fridge, owner, other, milk):
    response = client_for(owner).patch(
        item_url(fridge, milk),
        {"name": "Молоко домашнє", "category": "other", "opened_at": "2026-11-27"},
        format="json",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Молоко домашнє"
    assert body["category"] == "other"
    assert body["opened_at"] == "2026-11-27"
    assert StockMovement.objects.count() == 0


def test_patch_with_a_quantity_records_one_movement(fridge, owner, milk):
    response = client_for(owner).patch(
        item_url(fridge, milk),
        {"quantity": "350", "reason": "calories"},
        format="json",
    )

    assert response.status_code == 200
    assert quantity_of(response) == Decimal("350")
    movement = StockMovement.objects.get()
    assert movement.delta == Decimal("-150")
    assert movement.quantity_after == Decimal("350")
    assert movement.reason == StockReason.CALORIES
    assert movement.user == owner


def test_patch_cannot_set_the_quantity_to_zero(fridge, owner, milk):
    response = client_for(owner).patch(
        item_url(fridge, milk), {"quantity": "0"}, format="json"
    )

    assert response.status_code == 400
    assert "quantity" in response.json()["fields"]
    milk.refresh_from_db()
    assert milk.quantity == Decimal("500")


def test_patch_does_not_change_the_unit(fridge, owner, milk):
    response = client_for(owner).patch(
        item_url(fridge, milk), {"unit": "l"}, format="json"
    )

    assert response.status_code == 200
    milk.refresh_from_db()
    assert milk.unit == "ml"


def test_patch_can_clear_the_expiry_date(fridge, owner, dairy):
    item = make_item(fridge, dairy, expires_at="2026-12-05")

    response = client_for(owner).patch(
        item_url(fridge, item), {"expires_at": None}, format="json"
    )

    assert response.status_code == 200
    assert response.json()["expires_at"] is None


def test_patch_refuses_an_unknown_category(fridge, owner, milk):
    response = client_for(owner).patch(
        item_url(fridge, milk), {"category": "x"}, format="json"
    )

    assert response.status_code == 400
    assert "category" in response.json()["fields"]


# --- removing ---


def test_delete_removes_the_item_and_records_it(fridge, owner, milk):
    response = client_for(owner).delete(item_url(fridge, milk))

    assert response.status_code == 204
    assert FridgeItem.objects.count() == 0
    movement = StockMovement.objects.get()
    assert movement.delta == Decimal("-500")
    assert movement.quantity_after == Decimal("0")
    assert movement.item is None


def test_delete_of_a_removed_item_is_not_found(fridge, owner, milk):
    api_client = client_for(owner)
    api_client.delete(item_url(fridge, milk))

    response = api_client.delete(item_url(fridge, milk))

    assert response.status_code == 404


# --- consuming ---


def test_consume_takes_an_amount_out(fridge, owner, milk):
    response = client_for(owner).post(
        consume_url(fridge, milk), {"amount": "200", "reason": "recipe"}, format="json"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["removed"] is False
    assert Decimal(body["item"]["quantity"]) == Decimal("300")
    movement = StockMovement.objects.get()
    assert movement.delta == Decimal("-200")
    assert movement.reason == StockReason.RECIPE
    assert movement.user == owner


def test_consuming_everything_removes_the_item(fridge, owner, milk):
    response = client_for(owner).post(
        consume_url(fridge, milk), {"amount": "500"}, format="json"
    )

    assert response.status_code == 200
    assert response.json() == {"removed": True, "item": None}
    assert FridgeItem.objects.count() == 0
    movement = StockMovement.objects.get()
    assert movement.quantity_after == Decimal("0")
    assert movement.item_name == "Молоко"
    assert movement.item is None


def test_consuming_more_than_there_is_is_refused(fridge, owner, milk):
    response = client_for(owner).post(
        consume_url(fridge, milk), {"amount": "500.5"}, format="json"
    )

    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "quantity_negative"
    assert Decimal(body["available"]) == Decimal("500")
    assert "500" in body["detail"]
    milk.refresh_from_db()
    assert milk.quantity == Decimal("500")
    assert StockMovement.objects.count() == 0


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"amount": "0"},
        {"amount": "-1"},
        {"amount": "abc"},
        {"amount": "1", "reason": "x"},
    ],
)
def test_consume_refuses_bad_data(fridge, owner, milk, payload):
    response = client_for(owner).post(consume_url(fridge, milk), payload, format="json")

    assert response.status_code == 400
    assert response.json()["code"] == "validation_error"
    assert StockMovement.objects.count() == 0


# --- the fridge list shows the count ---


def test_the_fridge_list_counts_the_items(fridge, owner, dairy, milk):
    make_item(fridge, dairy, name="Кефір")

    response = client_for(owner).get("/api/fridges/")

    entry = next(item for item in response.json() if item["id"] == str(fridge.pk))
    assert entry["product_count"] == 2


# --- the names of bulk errors ---


def test_flatten_error_details_names_the_line_and_the_field():
    errors = {"reason": ["Bad."], "items": [{}, {"quantity": ["Too small."]}]}

    fields = flatten_error_details(errors)

    assert fields == {"reason": ["Bad."], "items.1.quantity": ["Too small."]}


def test_flatten_error_details_reads_errors_keyed_by_line():
    errors = {"items": {"2": {"unit": ["Bad unit."]}}}

    fields = flatten_error_details(errors)

    assert fields == {"items.2.unit": ["Bad unit."]}


@pytest.mark.parametrize(
    "errors",
    [{"items": ["Empty."]}, {"items": {"non_field_errors": ["Empty."]}}],
)
def test_flatten_error_details_keeps_list_errors_under_the_list_name(errors):
    assert flatten_error_details(errors) == {"items": ["Empty."]}
