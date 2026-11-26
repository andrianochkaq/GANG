import uuid

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.fridges.models import Fridge, FridgeMembership, MembershipStatus
from apps.fridges.services import DEFAULT_FRIDGE_NAME, create_fridge

pytestmark = pytest.mark.django_db

LIST_URL = "/api/fridges/"


def detail_url(fridge_id):
    return f"{LIST_URL}{fridge_id}/"


def make_user(nickname):
    return User.objects.create_user(nickname, email=f"{nickname}@example.com")


def add_member(fridge, user, status=MembershipStatus.ACTIVE):
    return FridgeMembership.objects.create(fridge=fridge, user=user, status=status)


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


def listed_names(user):
    return [item["name"] for item in client_for(user).get(LIST_URL).json()]


# --- the list ---


def test_list_requires_a_login():
    response = APIClient().get(LIST_URL)

    assert response.status_code == 401


def test_new_user_sees_the_default_fridge_as_current(owner):
    body = client_for(owner).get(LIST_URL).json()

    assert [item["name"] for item in body] == [DEFAULT_FRIDGE_NAME]
    assert body[0]["is_current"] is True
    assert body[0]["role"] == "owner"


def test_list_shows_the_fields_of_a_fridge(owner, fridge, member):
    response = client_for(owner).get(LIST_URL)

    assert response.status_code == 200
    item = next(item for item in response.json() if item["id"] == str(fridge.pk))
    assert set(item) == {
        "id",
        "name",
        "role",
        "member_count",
        "product_count",
        "is_current",
        "created_at",
    }
    assert item["name"] == "Дача"
    assert item["role"] == "owner"
    assert item["member_count"] == 2
    assert item["product_count"] == 0


def test_list_shows_the_role_of_a_member(member, fridge):
    items = client_for(member).get(LIST_URL).json()

    shared = next(item for item in items if item["id"] == str(fridge.pk))
    assert shared["role"] == "member"


def test_list_counts_only_active_members(owner, fridge):
    add_member(fridge, make_user("petro"), status=MembershipStatus.PENDING)

    items = client_for(owner).get(LIST_URL).json()

    item = next(item for item in items if item["id"] == str(fridge.pk))
    assert item["member_count"] == 1


def test_list_hides_other_peoples_and_pending_fridges(owner, fridge):
    stranger = make_user("olga")
    guest = make_user("petro")
    add_member(fridge, guest, status=MembershipStatus.PENDING)

    assert "Дача" not in listed_names(stranger)
    assert "Дача" not in listed_names(guest)


def test_list_marks_exactly_one_fridge_as_current(owner, fridge):
    items = client_for(owner).get(LIST_URL).json()

    assert [item["is_current"] for item in items].count(True) == 1


# --- creating ---


def test_create_makes_the_user_the_owner(owner):
    response = client_for(owner).post(LIST_URL, {"name": "  Квартира  "}, format="json")

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Квартира"
    assert body["role"] == "owner"
    assert body["member_count"] == 1
    fridge = Fridge.objects.get(pk=body["id"])
    assert fridge.owner == owner
    membership = FridgeMembership.objects.get(fridge=fridge, user=owner)
    assert membership.status == MembershipStatus.ACTIVE


@pytest.mark.parametrize(
    "body", [{}, {"name": ""}, {"name": "   "}, {"name": "а" * 101}]
)
def test_create_rejects_a_missing_blank_or_long_name(owner, body):
    response = client_for(owner).post(LIST_URL, body, format="json")

    assert response.status_code == 400
    assert response.json()["code"] == "validation_error"
    assert "name" in response.json()["fields"]


# --- viewing ---


def test_member_views_a_fridge(member, fridge):
    response = client_for(member).get(detail_url(fridge.pk))

    assert response.status_code == 200
    assert response.json()["name"] == "Дача"
    assert response.json()["role"] == "member"


def test_stranger_gets_404_for_a_fridge(fridge):
    response = client_for(make_user("petro")).get(detail_url(fridge.pk))

    assert response.status_code == 404


def test_pending_member_gets_404_for_a_fridge(fridge):
    guest = make_user("petro")
    add_member(fridge, guest, status=MembershipStatus.PENDING)

    response = client_for(guest).get(detail_url(fridge.pk))

    assert response.status_code == 404


@pytest.mark.parametrize("fridge_id", [uuid.uuid4(), "not-a-uuid"])
def test_unknown_fridge_gets_404(owner, fridge_id):
    response = client_for(owner).get(detail_url(fridge_id))

    assert response.status_code == 404


# --- renaming ---


def test_owner_renames_a_fridge(owner, fridge):
    response = client_for(owner).patch(
        detail_url(fridge.pk),
        {"name": "Нова дача"},
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Нова дача"
    fridge.refresh_from_db()
    assert fridge.name == "Нова дача"


def test_member_cannot_rename_a_fridge(member, fridge):
    response = client_for(member).patch(
        detail_url(fridge.pk),
        {"name": "Моє"},
        format="json",
    )

    assert response.status_code == 403
    assert response.json()["code"] == "fridge_owner_only"
    fridge.refresh_from_db()
    assert fridge.name == "Дача"


def test_stranger_cannot_rename_a_fridge(fridge):
    response = client_for(make_user("petro")).patch(
        detail_url(fridge.pk),
        {"name": "Моє"},
        format="json",
    )

    assert response.status_code == 404


def test_rename_rejects_a_blank_name(owner, fridge):
    response = client_for(owner).patch(
        detail_url(fridge.pk), {"name": " "}, format="json"
    )

    assert response.status_code == 400
    assert response.json()["code"] == "validation_error"


def test_put_is_not_allowed(owner, fridge):
    response = client_for(owner).put(
        detail_url(fridge.pk), {"name": "Нова"}, format="json"
    )

    assert response.status_code == 405


# --- deleting ---


def test_owner_deletes_a_fridge_without_other_members(owner, fridge):
    response = client_for(owner).delete(detail_url(fridge.pk))

    assert response.status_code == 204
    assert not Fridge.objects.filter(pk=fridge.pk).exists()
    assert "Дача" not in listed_names(owner)


def test_owner_cannot_delete_a_fridge_with_other_members(owner, fridge, member):
    response = client_for(owner).delete(detail_url(fridge.pk))

    assert response.status_code == 409
    assert response.json()["code"] == "fridge_has_members"
    assert Fridge.objects.filter(pk=fridge.pk).exists()


def test_pending_request_does_not_stop_the_owner_from_deleting(owner, fridge):
    add_member(fridge, make_user("petro"), status=MembershipStatus.PENDING)

    response = client_for(owner).delete(detail_url(fridge.pk))

    assert response.status_code == 204


def test_member_cannot_delete_a_fridge(member, fridge):
    response = client_for(member).delete(detail_url(fridge.pk))

    assert response.status_code == 403
    assert response.json()["code"] == "fridge_owner_only"
    assert Fridge.objects.filter(pk=fridge.pk).exists()


def test_stranger_cannot_delete_a_fridge(fridge):
    response = client_for(make_user("petro")).delete(detail_url(fridge.pk))

    assert response.status_code == 404
    assert Fridge.objects.filter(pk=fridge.pk).exists()


# --- leaving ---


def test_member_leaves_and_the_fridge_leaves_their_list(member, fridge):
    response = client_for(member).post(f"{detail_url(fridge.pk)}leave/")

    assert response.status_code == 204
    assert "Дача" not in listed_names(member)
    assert Fridge.objects.filter(pk=fridge.pk).exists()
    assert client_for(member).get(detail_url(fridge.pk)).status_code == 404


def test_owner_cannot_leave(owner, fridge):
    response = client_for(owner).post(f"{detail_url(fridge.pk)}leave/")

    assert response.status_code == 409
    assert response.json()["code"] == "owner_cannot_leave"
    assert "Дача" in listed_names(owner)


def test_stranger_cannot_leave_a_fridge(fridge):
    response = client_for(make_user("petro")).post(f"{detail_url(fridge.pk)}leave/")

    assert response.status_code == 404


# --- remembering the current fridge ---


def test_selecting_a_fridge_makes_it_current(owner, fridge):
    api_client = client_for(owner)

    response = api_client.post(f"{detail_url(fridge.pk)}select/")

    assert response.status_code == 200
    assert response.json()["is_current"] is True
    owner.refresh_from_db()
    assert owner.last_fridge == fridge
    current_names = [
        item["name"] for item in api_client.get(LIST_URL).json() if item["is_current"]
    ]
    assert current_names == ["Дача"]


def test_selection_is_remembered_in_a_new_session(owner, fridge):
    client_for(owner).post(f"{detail_url(fridge.pk)}select/")

    items = client_for(User.objects.get(pk=owner.pk)).get(LIST_URL).json()

    assert [item["name"] for item in items if item["is_current"]] == ["Дача"]


def test_member_can_select_a_shared_fridge(member, fridge):
    response = client_for(member).post(f"{detail_url(fridge.pk)}select/")

    assert response.status_code == 200
    assert response.json()["is_current"] is True


def test_stranger_cannot_select_a_fridge(fridge):
    stranger = make_user("petro")

    response = client_for(stranger).post(f"{detail_url(fridge.pk)}select/")

    assert response.status_code == 404
    stranger.refresh_from_db()
    assert stranger.last_fridge is None


def test_current_fridge_moves_on_after_leaving_it(member, fridge):
    api_client = client_for(member)
    api_client.post(f"{detail_url(fridge.pk)}select/")

    api_client.post(f"{detail_url(fridge.pk)}leave/")

    items = api_client.get(LIST_URL).json()
    assert [item["name"] for item in items if item["is_current"]] == [
        DEFAULT_FRIDGE_NAME
    ]
