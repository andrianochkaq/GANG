import uuid

import pytest
from rest_framework import serializers
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.fridges.models import Fridge, FridgeMembership, MembershipStatus
from apps.fridges.permissions import IsFridgeMember
from apps.fridges.services import create_fridge

pytestmark = pytest.mark.django_db


class FridgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fridge
        fields = ["id", "name"]


class FridgeDetailView(RetrieveAPIView):
    queryset = Fridge.objects.all()
    serializer_class = FridgeSerializer
    permission_classes = [IsFridgeMember]


class FridgeItemsView(APIView):
    permission_classes = [IsFridgeMember]

    def get(self, request, fridge_id):
        return Response({"fridge_id": str(fridge_id)})


def make_user(nickname):
    return User.objects.create_user(nickname, email=f"{nickname}@example.com")


def call(view, user, **kwargs):
    request = APIRequestFactory().get("/")
    if user is not None:
        force_authenticate(request, user=user)
    return view(request, **kwargs)


@pytest.fixture
def owner():
    return make_user("anna")


@pytest.fixture
def fridge(owner):
    return create_fridge(owner, "Дача")


def test_active_member_sees_the_fridge(fridge, owner):
    response = call(FridgeDetailView.as_view(), owner, pk=fridge.pk)

    assert response.status_code == 200
    assert response.data["name"] == "Дача"


def test_non_member_gets_404_for_another_users_fridge(fridge):
    stranger = make_user("olga")

    response = call(FridgeDetailView.as_view(), stranger, pk=fridge.pk)

    assert response.status_code == 404


def test_pending_member_gets_404(fridge):
    guest = make_user("olga")
    FridgeMembership.objects.create(fridge=fridge, user=guest)

    response = call(FridgeDetailView.as_view(), guest, pk=fridge.pk)

    assert response.status_code == 404


def test_member_becomes_able_to_see_the_fridge_once_active(fridge):
    guest = make_user("olga")
    FridgeMembership.objects.create(
        fridge=fridge,
        user=guest,
        status=MembershipStatus.ACTIVE,
    )

    response = call(FridgeDetailView.as_view(), guest, pk=fridge.pk)

    assert response.status_code == 200


def test_anonymous_user_is_refused(fridge):
    response = call(FridgeDetailView.as_view(), None, pk=fridge.pk)

    assert response.status_code in (401, 403)


def test_fridge_id_in_the_url_is_checked_for_members(fridge, owner):
    response = call(FridgeItemsView.as_view(), owner, fridge_id=fridge.pk)

    assert response.status_code == 200


def test_fridge_id_in_the_url_gives_404_to_non_members(fridge):
    stranger = make_user("olga")

    response = call(FridgeItemsView.as_view(), stranger, fridge_id=fridge.pk)

    assert response.status_code == 404


def test_unknown_fridge_id_gives_404(owner):
    response = call(FridgeItemsView.as_view(), owner, fridge_id=uuid.uuid4())

    assert response.status_code == 404


def test_malformed_fridge_id_gives_404(owner):
    response = call(FridgeItemsView.as_view(), owner, fridge_id="not-a-uuid")

    assert response.status_code == 404
