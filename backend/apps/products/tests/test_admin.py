import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.products.models import CatalogProduct, Category

pytestmark = pytest.mark.django_db

TEST_PASSWORD = "correct-horse-battery-staple"


@pytest.fixture
def admin_session(client):
    superuser = User.objects.create_superuser(
        "root",
        password=TEST_PASSWORD,
        email="root@example.com",
    )
    client.force_login(superuser)
    return client


@pytest.fixture
def condensed_milk():
    category = Category.objects.create(slug="dairy", name="Молочне")
    return CatalogProduct.objects.create(
        name="Молоко згущене",
        aliases=["згущівка"],
        category=category,
        default_unit="g",
        kcal_per_100g="320",
        protein_per_100g="7.2",
        fat_per_100g="8.5",
        carbs_per_100g="56",
        default_shelf_days=365,
    )


def read_page(response):
    assert response.status_code == 200
    return response.content.decode()


def test_categories_are_listed_in_the_admin(admin_session, condensed_milk):
    response = admin_session.get(reverse("admin:products_category_changelist"))

    assert "Молочне" in read_page(response)


def test_catalog_products_are_listed_in_the_admin(admin_session, condensed_milk):
    url = reverse("admin:products_catalogproduct_changelist")

    page = read_page(admin_session.get(url))

    assert "Молоко згущене" in page


def test_catalog_products_can_be_found_by_name(admin_session, condensed_milk):
    url = reverse("admin:products_catalogproduct_changelist")

    page = read_page(admin_session.get(url, {"q": "згущене"}))

    assert "Молоко згущене" in page


def test_catalog_products_can_be_found_by_alias(admin_session, condensed_milk):
    url = reverse("admin:products_catalogproduct_changelist")

    page = read_page(admin_session.get(url, {"q": "згущівка"}))

    assert "Молоко згущене" in page


def test_a_search_with_no_match_hides_the_product(admin_session, condensed_milk):
    url = reverse("admin:products_catalogproduct_changelist")

    page = read_page(admin_session.get(url, {"q": "огірок"}))

    assert "Молоко згущене" not in page


def test_a_catalog_product_can_be_opened_in_the_admin(admin_session, condensed_milk):
    url = reverse("admin:products_catalogproduct_change", args=[condensed_milk.pk])

    page = read_page(admin_session.get(url))

    assert "Молоко згущене" in page
