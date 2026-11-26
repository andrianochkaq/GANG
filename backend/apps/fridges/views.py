"""The fridges API: list, create, view, rename, delete, leave, select.

Everything is scoped to the fridges where the user is an active member, and
anybody else gets 404 (``IsFridgeMember``). Renaming and deleting are for
the owner only: a member who sees the fridge gets 403.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.accounts.serializers import ApiErrorSerializer
from apps.accounts.views.responses import (
    build_error_response,
    build_validation_error_response,
)

from .models import Fridge
from .permissions import IsFridgeMember
from .serializers import FridgeNameSerializer, FridgeSerializer
from .services import (
    FridgeHasMembersError,
    OwnerCannotLeaveError,
    annotate_fridge_summary,
    create_fridge,
    delete_fridge,
    find_current_fridge_id,
    leave_fridge,
    select_fridge,
)


class FridgeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    permission_classes = [IsFridgeMember]
    serializer_class = FridgeSerializer
    pagination_class = None
    lookup_url_kwarg = "fridge_id"
    lookup_value_regex = "[0-9a-fA-F-]{36}"
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        fridges = Fridge.objects.visible_to(self.request.user)
        return annotate_fridge_summary(fridges).order_by("created_at", "pk")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["current_fridge_id"] = find_current_fridge_id(self.request.user)
        return context

    @extend_schema(
        request=FridgeNameSerializer,
        responses={
            201: FridgeSerializer,
            400: ApiErrorSerializer,
        },
        summary="Create a fridge; the user becomes its owner",
    )
    def create(self, request):
        serializer = FridgeNameSerializer(data=request.data)
        if not serializer.is_valid():
            return build_validation_error_response(serializer)
        fridge = create_fridge(request.user, serializer.validated_data["name"])
        return self._build_fridge_response(fridge, status.HTTP_201_CREATED)

    @extend_schema(
        request=FridgeNameSerializer,
        responses={
            200: FridgeSerializer,
            400: ApiErrorSerializer,
            403: ApiErrorSerializer,
        },
        summary="Rename a fridge (owner only)",
    )
    def partial_update(self, request, fridge_id):
        fridge = self.get_object()
        if fridge.owner_id != request.user.pk:
            return _build_owner_only_response()
        serializer = FridgeNameSerializer(data=request.data)
        if not serializer.is_valid():
            return build_validation_error_response(serializer)
        fridge.name = serializer.validated_data["name"]
        fridge.save(update_fields=["name"])
        return self._build_fridge_response(fridge, status.HTTP_200_OK)

    @extend_schema(
        responses={
            204: None,
            403: ApiErrorSerializer,
            409: ApiErrorSerializer,
        },
        summary="Delete a fridge that has no other members (owner only)",
    )
    def destroy(self, request, fridge_id):
        fridge = self.get_object()
        if fridge.owner_id != request.user.pk:
            return _build_owner_only_response()
        try:
            delete_fridge(fridge)
        except FridgeHasMembersError:
            return build_error_response(
                "fridge_has_members",
                "У холодильнику є інші учасники. "
                "Видалити його можна, коли вони його залишать.",
                status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        request=None,
        responses={204: None, 409: ApiErrorSerializer},
        summary="Leave a fridge (a member; the owner cannot)",
    )
    @action(detail=True, methods=["post"], url_path="leave")
    def leave(self, request, fridge_id):
        fridge = self.get_object()
        try:
            leave_fridge(request.user, fridge)
        except OwnerCannotLeaveError:
            return build_error_response(
                "owner_cannot_leave",
                "Власник не може залишити холодильник. "
                "Видаліть його, коли в ньому нікого не залишиться.",
                status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        request=None,
        responses={200: FridgeSerializer},
        summary="Remember the fridge as the one the user works in",
    )
    @action(detail=True, methods=["post"], url_path="select")
    def select(self, request, fridge_id):
        fridge = self.get_object()
        select_fridge(request.user, fridge)
        return self._build_fridge_response(fridge, status.HTTP_200_OK)

    def _build_fridge_response(self, fridge, http_status):
        # Load it again with the counts that the serializer shows.
        fridge = self.get_queryset().get(pk=fridge.pk)
        serializer = self.get_serializer(fridge)
        return Response(serializer.data, status=http_status)


def _build_owner_only_response():
    return build_error_response(
        "fridge_owner_only",
        "Це може зробити лише власник холодильника.",
        status.HTTP_403_FORBIDDEN,
    )
