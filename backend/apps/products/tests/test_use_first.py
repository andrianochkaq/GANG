from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.fridges.services import create_fridge
from apps.products.models import FridgeItem
from apps.products.services.use_first import (
    USE_FIRST_LIMIT,
    list_use_first_items,
)
from apps.products.tests.factories import make_category, make_item, make_user

pytestmark = pytest.mark.django_db


@pytest.fixture
def owner():
    return make_user("anna")


@pytest.fixture
def fridge(owner):
    return create_fridge(owner, "Дача")


@pytest.fixture
def dairy():
    return make_category("dairy", "Молочне")


def use_first_url(fridge):
    return f"/api/fridges/{fridge.pk}/items/use-first/"


def days_from_today(days):
    return timezone.localdate() + timedelta(days=days)


def names_of(items):
    return [item.name for item in items]


def test_expired_items_come_first(fridge, dairy):
    make_item(fridge, dairy, name="Свіже", expires_at=days_from_today(1))
    make_item(fridge, dairy, name="Прострочене", expires_at=days_from_today(-2))

    found = list_use_first_items(FridgeItem.objects.filter(fridge=fridge))

    assert names_of(found) == ["Прострочене", "Свіже"]


def test_item_expiring_tomorrow_is_above_one_expiring_in_three_days(fridge, dairy):
    make_item(fridge, dairy, name="Через три дні", expires_at=days_from_today(3))
    make_item(fridge, dairy, name="Завтра", expires_at=days_from_today(1))

    found = list_use_first_items(FridgeItem.objects.filter(fridge=fridge))

    assert names_of(found) == ["Завтра", "Через три дні"]


def test_item_expiring_today_is_not_expired_but_is_soon(fridge, dairy):
    make_item(fridge, dairy, name="Сьогодні", expires_at=days_from_today(0))
    make_item(fridge, dairy, name="Вчора", expires_at=days_from_today(-1))

    found = list_use_first_items(FridgeItem.objects.filter(fridge=fridge))

    assert names_of(found) == ["Вчора", "Сьогодні"]


def test_full_order_expired_soon_opened_then_oldest(fridge, dairy):
    now = timezone.now()
    make_item(fridge, dairy, name="Старе", created_at=now - timedelta(days=9))
    make_item(fridge, dairy, name="Нове", created_at=now - timedelta(days=1))
    make_item(
        fridge,
        dairy,
        name="Відкрите",
        opened_at=days_from_today(-1),
        created_at=now - timedelta(days=5),
    )
    make_item(fridge, dairy, name="Скоро", expires_at=days_from_today(2))
    make_item(fridge, dairy, name="Минуло", expires_at=days_from_today(-5))
    make_item(fridge, dairy, name="Далеко", expires_at=days_from_today(30))

    found = list_use_first_items(FridgeItem.objects.filter(fridge=fridge))

    assert names_of(found)[:4] == ["Минуло", "Скоро", "Відкрите", "Старе"]
    assert set(names_of(found)[4:]) == {"Нове", "Далеко"}


def test_item_expiring_later_than_three_days_but_opened_counts_as_opened(fridge, dairy):
    now = timezone.now()
    make_item(fridge, dairy, name="Просто", created_at=now - timedelta(days=9))
    make_item(
        fridge,
        dairy,
        name="Відкрите",
        expires_at=days_from_today(20),
        opened_at=days_from_today(-1),
        created_at=now,
    )

    found = list_use_first_items(FridgeItem.objects.filter(fridge=fridge))

    assert names_of(found) == ["Відкрите", "Просто"]


def test_the_list_is_cut_at_the_limit(fridge, dairy):
    for number in range(3):
        make_item(fridge, dairy, name=f"Продукт {number}")

    found = list_use_first_items(FridgeItem.objects.filter(fridge=fridge), limit=2)

    assert len(found) == 2
    assert USE_FIRST_LIMIT == 50


def test_endpoint_lists_urgent_items_first_for_a_member(owner, fridge, dairy):
    make_item(fridge, dairy, name="Через три дні", expires_at=days_from_today(3))
    make_item(fridge, dairy, name="Завтра", expires_at=days_from_today(1))
    make_item(fridge, dairy, name="Прострочене", expires_at=days_from_today(-1))
    api_client = APIClient()
    api_client.force_authenticate(user=owner)

    response = api_client.get(use_first_url(fridge))

    assert response.status_code == 200
    names = [item["name"] for item in response.json()["items"]]
    assert names == ["Прострочене", "Завтра", "Через три дні"]


def test_endpoint_ignores_items_of_other_fridges(owner, fridge, dairy):
    other_fridge = create_fridge(make_user("olga"), "Квартира")
    make_item(other_fridge, dairy, name="Чуже", expires_at=days_from_today(-1))
    make_item(fridge, dairy, name="Своє")
    api_client = APIClient()
    api_client.force_authenticate(user=owner)

    response = api_client.get(use_first_url(fridge))

    assert [item["name"] for item in response.json()["items"]] == ["Своє"]


def test_endpoint_requires_a_login(fridge):
    response = APIClient().get(use_first_url(fridge))

    assert response.status_code == 401


def test_a_stranger_gets_404(fridge, dairy):
    make_item(fridge, dairy)
    api_client = APIClient()
    api_client.force_authenticate(user=make_user("petro"))

    response = api_client.get(use_first_url(fridge))

    assert response.status_code == 404
