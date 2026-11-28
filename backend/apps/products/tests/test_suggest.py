import time

import pytest
from rest_framework.test import APIClient

from apps.fridges.models import MembershipStatus
from apps.fridges.services import create_fridge
from apps.products.services.catalog_loader import (
    DEFAULT_CATALOG_PATH,
    load_catalog_file,
)
from apps.products.tests.factories import (
    add_member,
    make_catalog_product,
    make_category,
    make_item,
    make_user,
)

pytestmark = pytest.mark.django_db

MAX_SECONDS = 0.3


def suggestions_url(fridge):
    return f"/api/fridges/{fridge.pk}/items/suggestions/"


def client_for(user):
    api_client = APIClient()
    api_client.force_authenticate(user=user)
    return api_client


def ask(user, fridge, text=None):
    params = {} if text is None else {"q": text}
    return client_for(user).get(suggestions_url(fridge), params)


def names_of(response):
    return [entry["name"] for entry in response.json()["suggestions"]]


def make_product_with_aliases(category, name, aliases):
    product = make_catalog_product(category, name=name)
    product.aliases = aliases
    product.save(update_fields=["aliases"])
    return product


@pytest.fixture
def owner():
    return make_user("anna")


@pytest.fixture
def fridge(owner):
    return create_fridge(owner, "Дача")


@pytest.fixture
def dairy():
    return make_category("dairy", "Молочне")


@pytest.fixture
def vegetables():
    return make_category("vegetables", "Овочі")


# --- who can ask ---


def test_a_login_is_required(fridge):
    response = APIClient().get(suggestions_url(fridge), {"q": "мо"})

    assert response.status_code == 401


def test_a_stranger_gets_404(fridge):
    stranger = make_user("petro")

    response = ask(stranger, fridge, "мо")

    assert response.status_code == 404


def test_a_member_whose_request_is_pending_gets_404(fridge):
    applicant = make_user("ivan")
    add_member(fridge, applicant, status=MembershipStatus.PENDING)

    response = ask(applicant, fridge, "мо")

    assert response.status_code == 404


def test_an_active_member_can_ask(fridge, dairy):
    member = make_user("olga")
    add_member(fridge, member)
    make_catalog_product(dairy, name="Молоко")

    response = ask(member, fridge, "мо")

    assert response.status_code == 200
    assert names_of(response) == ["Молоко"]


# --- the text ---


def test_no_text_gives_no_suggestions(owner, fridge, dairy):
    make_catalog_product(dairy, name="Молоко")

    assert ask(owner, fridge).json() == {"suggestions": []}
    assert ask(owner, fridge, "").json() == {"suggestions": []}
    assert ask(owner, fridge, "   ").json() == {"suggestions": []}


def test_text_longer_than_a_name_is_refused(owner, fridge):
    response = ask(owner, fridge, "а" * 121)

    assert response.status_code == 400


def test_percent_and_underscore_are_plain_characters(owner, fridge, dairy):
    make_product_with_aliases(dairy, "Молоко", ["молочко"])
    make_item(fridge, dairy, name="Кефір")

    assert names_of(ask(owner, fridge, "%")) == []
    assert names_of(ask(owner, fridge, "_")) == []
    assert names_of(ask(owner, fridge, "\\")) == []


# --- catalog products ---


def test_mo_gives_milk_and_carrot(owner, fridge, dairy, vegetables):
    make_catalog_product(dairy, name="Молоко 2,5%")
    make_catalog_product(vegetables, name="Морква")
    make_catalog_product(vegetables, name="Огірок")

    response = ask(owner, fridge, "мо")

    assert names_of(response) == ["Морква", "Молоко 2,5%"]


def test_prefix_ignores_case(owner, fridge, dairy):
    make_catalog_product(dairy, name="Молоко")

    assert names_of(ask(owner, fridge, "МО")) == ["Молоко"]
    assert names_of(ask(owner, fridge, "мОл")) == ["Молоко"]


def test_shorter_names_come_first_among_prefix_matches(owner, fridge, dairy):
    make_catalog_product(dairy, name="Молоко згущене")
    make_catalog_product(dairy, name="Молоко")
    make_catalog_product(dairy, name="Молоко 1%")

    response = ask(owner, fridge, "мол")

    assert names_of(response) == ["Молоко", "Молоко 1%", "Молоко згущене"]


def test_a_name_must_start_with_the_text(owner, fridge, dairy):
    make_catalog_product(dairy, name="Шоколадне молоко")

    assert names_of(ask(owner, fridge, "моло")) == []


def test_an_alias_that_starts_with_the_text_finds_the_product(owner, fridge, dairy):
    make_product_with_aliases(dairy, "Картопля", ["картошка", "бульба"])
    make_catalog_product(dairy, name="Огірок")

    assert names_of(ask(owner, fridge, "картош")) == ["Картопля"]
    assert names_of(ask(owner, fridge, "БУЛЬ")) == ["Картопля"]


def test_names_that_start_with_the_text_come_before_aliases(owner, fridge, dairy):
    make_product_with_aliases(dairy, "Картопля", ["картошка"])
    make_catalog_product(dairy, name="Картошка смажена")

    response = ask(owner, fridge, "картошка")

    assert names_of(response) == ["Картошка смажена", "Картопля"]


def test_a_product_is_not_offered_twice_for_name_and_alias(owner, fridge, dairy):
    make_product_with_aliases(dairy, "Молоко", ["молочко", "молоко пастеризоване"])

    assert names_of(ask(owner, fridge, "мол")) == ["Молоко"]


def test_prefix_matches_come_before_similar_ones(owner, fridge, dairy):
    make_catalog_product(dairy, name="Молочко")
    make_catalog_product(dairy, name="Молоко згущене")

    response = ask(owner, fridge, "молок")

    assert names_of(response) == ["Молоко згущене", "Молочко"]


def test_a_typo_finds_a_similar_product(owner, fridge, dairy):
    make_catalog_product(dairy, name="Молоко")
    make_catalog_product(dairy, name="Огірок")

    assert names_of(ask(owner, fridge, "молко")) == ["Молоко"]


def test_a_suggestion_describes_the_catalog_product(owner, fridge, dairy):
    milk = make_catalog_product(dairy, name="Молоко 2,5%", unit="ml")

    response = ask(owner, fridge, "мо")

    assert response.json() == {
        "suggestions": [
            {
                "source": "catalog",
                "name": "Молоко 2,5%",
                "unit": "ml",
                "category": "dairy",
                "catalog_product": str(milk.pk),
            }
        ]
    }


# --- items already in the fridge ---


def test_fridge_items_come_before_catalog_products(owner, fridge, dairy):
    make_catalog_product(dairy, name="Морква")
    make_catalog_product(dairy, name="Молоко")
    make_item(fridge, dairy, name="Морозиво", unit="g")

    response = ask(owner, fridge, "мо")

    assert names_of(response) == ["Морозиво", "Молоко", "Морква"]
    sources = [entry["source"] for entry in response.json()["suggestions"]]
    assert sources == ["fridge", "catalog", "catalog"]


def test_a_suggestion_describes_the_fridge_item(owner, fridge, dairy):
    make_item(fridge, dairy, name="Молоко", unit="l")

    response = ask(owner, fridge, "мо")

    assert response.json() == {
        "suggestions": [
            {
                "source": "fridge",
                "name": "Молоко",
                "unit": "l",
                "category": "dairy",
                "catalog_product": None,
            }
        ]
    }


def test_a_fridge_item_keeps_the_link_to_its_catalog_product(owner, fridge, dairy):
    milk = make_catalog_product(dairy, name="Молоко 2,5%")
    make_item(fridge, dairy, name="Молоко", catalog_product=milk)

    response = ask(owner, fridge, "мо")

    suggestion = response.json()["suggestions"][0]
    assert suggestion["catalog_product"] == str(milk.pk)


def test_a_catalog_product_the_fridge_has_is_not_offered_again(owner, fridge, dairy):
    milk = make_catalog_product(dairy, name="Молоко 2,5%")
    make_item(fridge, dairy, name="Моє молоко", catalog_product=milk)

    response = ask(owner, fridge, "мо")

    assert names_of(response) == ["Моє молоко"]


def test_a_catalog_name_equal_to_a_fridge_name_is_not_offered_again(
    owner, fridge, dairy
):
    make_catalog_product(dairy, name="Морква")
    make_item(fridge, dairy, name="морква", unit="g")

    response = ask(owner, fridge, "мор")

    assert names_of(response) == ["морква"]


def test_items_with_the_same_name_and_unit_are_offered_once(owner, fridge, dairy):
    make_item(fridge, dairy, name="Молоко", expires_at="2026-12-01")
    make_item(fridge, dairy, name="Молоко", expires_at="2026-12-05")

    assert names_of(ask(owner, fridge, "мо")) == ["Молоко"]


def test_the_same_name_in_another_unit_is_offered_separately(owner, fridge, dairy):
    make_item(fridge, dairy, name="Молоко", unit="ml")
    make_item(fridge, dairy, name="Молоко", unit="pack")

    response = ask(owner, fridge, "мо")

    units = sorted(entry["unit"] for entry in response.json()["suggestions"])
    assert units == ["ml", "pack"]


def test_a_similar_fridge_item_comes_before_a_closer_catalog_product(
    owner, fridge, dairy
):
    make_catalog_product(dairy, name="Молоко")
    make_item(fridge, dairy, name="Молочко")

    response = ask(owner, fridge, "молко")

    assert names_of(response) == ["Молочко", "Молоко"]


def test_items_of_another_fridge_are_not_offered(owner, fridge, dairy):
    neighbour = make_user("olga")
    other_fridge = create_fridge(neighbour, "Гараж")
    make_item(other_fridge, dairy, name="Мандарини", unit="g")

    assert names_of(ask(owner, fridge, "ман")) == []


# --- how many ---


def test_at_most_eight_suggestions(owner, fridge, dairy):
    for number in range(5):
        make_item(fridge, dairy, name=f"Моя річ {number}", unit="g")
    for number in range(12):
        make_catalog_product(dairy, name=f"Моя страва {number:02d}")

    response = ask(owner, fridge, "мо")

    assert len(names_of(response)) == 8
    assert names_of(response)[:5] == [f"Моя річ {number}" for number in range(5)]


def test_repeats_do_not_use_up_the_places(owner, fridge, dairy):
    for number in range(4):
        linked = make_catalog_product(dairy, name=f"Мо {number}")
        make_item(fridge, dairy, name=f"Моя річ {number}", catalog_product=linked)
    for name in ["Морс", "Мойва", "Морква", "Мортаделла", "Морозиво", "Моцарела"]:
        make_catalog_product(dairy, name=name)

    response = ask(owner, fridge, "мо")

    assert names_of(response) == [
        "Моя річ 0",
        "Моя річ 1",
        "Моя річ 2",
        "Моя річ 3",
        "Морс",
        "Мойва",
        "Морква",
        "Морозиво",
    ]


# --- the whole catalog ---


@pytest.fixture
def full_catalog():
    load_catalog_file(DEFAULT_CATALOG_PATH)


def test_mo_gives_milk_and_carrot_with_the_whole_catalog(owner, fridge, full_catalog):
    response = ask(owner, fridge, "мо")

    names = [name.lower() for name in names_of(response)]
    assert any(name.startswith("молоко") for name in names)
    assert any(name.startswith("морква") for name in names)
    assert len(names) <= 8


@pytest.mark.parametrize("text", ["мо", "молко", "картошка", "йогурт", "хл", "zz"])
def test_the_whole_catalog_answers_within_the_time_limit(
    owner, fridge, full_catalog, text
):
    ask(owner, fridge, text)

    started = time.perf_counter()
    response = ask(owner, fridge, text)
    seconds = time.perf_counter() - started

    assert response.status_code == 200
    assert seconds < MAX_SECONDS
