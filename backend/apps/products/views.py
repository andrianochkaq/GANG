"""The fridge items API: list, add, change, remove, consume, suggest, use first.

Everything lives under ``/api/fridges/<fridge_id>/items/`` and is open to
the active members of that fridge only; anybody else gets 404
(``IsFridgeMember``). The rules are in ``services/stock.py``; suggestions
are found by ``services/suggestions.py``.
"""

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.accounts.serializers import ApiErrorSerializer
from apps.accounts.views.responses import (
    build_error_response,
    build_validation_error_response,
)
from apps.fridges.models import Fridge
from apps.fridges.permissions import IsFridgeMember

from .models import FridgeItem, ProductUnit
from .pagination import FridgeItemCursorPagination
from .serializers import (
    FridgeItemBulkResponseSerializer,
    FridgeItemBulkSerializer,
    FridgeItemConsumeResponseSerializer,
    FridgeItemConsumeSerializer,
    FridgeItemCreateSerializer,
    FridgeItemSerializer,
    FridgeItemUpdateSerializer,
    ProductSuggestionListSerializer,
    ProductSuggestionQuerySerializer,
    ProductSuggestionSerializer,
    UseFirstListSerializer,
)
from .services.stock import (
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
from .services.suggestions import suggest_products
from .services.units import UnitConversionError
from .services.use_first import list_use_first_items


class FridgeItemViewSet(GenericViewSet):
    permission_classes = [IsFridgeMember]
    serializer_class = FridgeItemSerializer
    pagination_class = FridgeItemCursorPagination
    lookup_url_kwarg = "item_id"
    lookup_value_regex = "[0-9a-fA-F-]{36}"
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        items = FridgeItem.objects.select_related("category", "fridge")
        return items.filter(fridge_id=self.kwargs["fridge_id"])

    @extend_schema(
        parameters=[
            OpenApiParameter("category", str, description="Category slug"),
            OpenApiParameter("search", str, description="Part of the name"),
        ],
        responses={200: FridgeItemSerializer(many=True)},
        summary="List the items of a fridge",
    )
    def list(self, request, fridge_id):
        items = filter_items(
            self.get_queryset(),
            category_slug=request.query_params.get("category"),
            search=request.query_params.get("search"),
        )
        page = self.paginate_queryset(items)
        serializer = FridgeItemSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @extend_schema(
        responses={200: FridgeItemSerializer, 404: ApiErrorSerializer},
        summary="Show one item",
    )
    def retrieve(self, request, fridge_id, item_id):
        return Response(FridgeItemSerializer(self.get_object()).data)

    @extend_schema(
        request=FridgeItemCreateSerializer,
        responses={
            200: FridgeItemSerializer,
            201: FridgeItemSerializer,
            400: ApiErrorSerializer,
        },
        summary="Add a product; 200 when it raised an item that was there",
    )
    def create(self, request, fridge_id):
        serializer = FridgeItemCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return build_validation_error_response(serializer)
        line = dict(serializer.validated_data)
        reason = line.pop("reason")
        try:
            added = add_item(
                _get_fridge(fridge_id),
                request.user,
                reason=reason,
                **line,
            )
        except CategoryRequiredError:
            return _build_category_required_response()
        http_status = status.HTTP_201_CREATED if added.is_new else status.HTTP_200_OK
        return Response(FridgeItemSerializer(added.item).data, status=http_status)

    @extend_schema(
        request=FridgeItemBulkSerializer,
        responses={
            201: FridgeItemBulkResponseSerializer,
            400: ApiErrorSerializer,
        },
        summary="Add several products at once: all of them or none",
    )
    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk(self, request, fridge_id):
        serializer = FridgeItemBulkSerializer(data=request.data)
        if not serializer.is_valid():
            return _build_bulk_validation_error_response(serializer)
        lines = [dict(line) for line in serializer.validated_data["items"]]
        try:
            added = add_items(
                _get_fridge(fridge_id),
                request.user,
                lines,
                reason=serializer.validated_data["reason"],
            )
        except CategoryRequiredError:
            return _build_category_required_response()
        items = FridgeItemSerializer([entry.item for entry in added], many=True)
        return Response({"items": items.data}, status=status.HTTP_201_CREATED)

    @extend_schema(
        parameters=[
            OpenApiParameter("q", str, description="Text typed so far, up to 120"),
        ],
        responses={200: ProductSuggestionListSerializer, 400: ApiErrorSerializer},
        summary="Suggest up to 8 products while the person types",
    )
    @action(detail=False, methods=["get"], url_path="suggestions")
    def suggestions(self, request, fridge_id):
        serializer = ProductSuggestionQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return build_validation_error_response(serializer)
        found = suggest_products(fridge_id, serializer.validated_data["q"])
        data = ProductSuggestionSerializer(found, many=True).data
        return Response({"suggestions": data})

    @extend_schema(
        responses={200: UseFirstListSerializer, 404: ApiErrorSerializer},
        summary="Items to use first: expired, expiring soon, opened, oldest",
    )
    @action(detail=False, methods=["get"], url_path="use-first")
    def use_first(self, request, fridge_id):
        found = list_use_first_items(self.get_queryset())
        return Response({"items": FridgeItemSerializer(found, many=True).data})

    @extend_schema(
        request=FridgeItemUpdateSerializer,
        responses={
            200: FridgeItemSerializer,
            400: ApiErrorSerializer,
            404: ApiErrorSerializer,
        },
        summary="Change an item; a new quantity is recorded in the history",
    )
    def partial_update(self, request, fridge_id, item_id):
        item = self.get_object()
        serializer = FridgeItemUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return build_validation_error_response(serializer)
        changes = dict(serializer.validated_data)
        reason = changes.pop("reason")
        try:
            updated_item = update_item(item, request.user, reason=reason, **changes)
        except ItemNotFoundError:
            return _build_item_not_found_response()
        return Response(FridgeItemSerializer(updated_item).data)

    @extend_schema(
        responses={204: None, 404: ApiErrorSerializer},
        summary="Remove an item; what was left is recorded in the history",
    )
    def destroy(self, request, fridge_id, item_id):
        item = self.get_object()
        try:
            delete_item(item, request.user)
        except ItemNotFoundError:
            return _build_item_not_found_response()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        request=FridgeItemConsumeSerializer,
        responses={
            200: FridgeItemConsumeResponseSerializer,
            400: ApiErrorSerializer,
            404: ApiErrorSerializer,
        },
        summary="Take an amount out; an item used up is removed",
    )
    @action(detail=True, methods=["post"], url_path="consume")
    def consume(self, request, fridge_id, item_id):
        item = self.get_object()
        serializer = FridgeItemConsumeSerializer(data=request.data)
        if not serializer.is_valid():
            return build_validation_error_response(serializer)
        try:
            remaining_item = consume_item(
                item,
                request.user,
                serializer.validated_data["amount"],
                reason=serializer.validated_data["reason"],
                unit=serializer.validated_data.get("unit"),
            )
        except QuantityBelowZeroError as error:
            return _build_quantity_negative_response(item, error.available)
        except UnitConversionError as error:
            return _build_unit_conversion_response(error)
        except ItemNotFoundError:
            return _build_item_not_found_response()
        item_data = None
        if remaining_item is not None:
            item_data = FridgeItemSerializer(remaining_item).data
        return Response({"removed": remaining_item is None, "item": item_data})


def _get_fridge(fridge_id):
    # IsFridgeMember has already checked that the fridge exists.
    return Fridge.objects.get(pk=fridge_id)


def flatten_error_details(errors, path="", fields=None):
    """Turn nested serializer errors into ``{"items.1.quantity": [...]}``.

    The errors of a list of lines come as a list with one entry per line or
    as a dict keyed by the line number, depending on the DRF version; both
    give the same names. Errors of the list itself stay under its name.
    """
    fields = {} if fields is None else fields
    if isinstance(errors, dict):
        for key, value in errors.items():
            flatten_error_details(value, _join_error_path(path, key), fields)
    elif isinstance(errors, list):
        for position, entry in enumerate(errors):
            if isinstance(entry, str):
                fields.setdefault(path, []).append(str(entry))
            else:
                entry_path = _join_error_path(path, position)
                flatten_error_details(entry, entry_path, fields)
    else:
        fields.setdefault(path, []).append(str(errors))
    return fields


def _join_error_path(path, key):
    if key == "non_field_errors":
        return path
    return f"{path}.{key}" if path else str(key)


def _build_bulk_validation_error_response(serializer):
    """Name the line and the field of every error: ``items.2.quantity``."""
    response = build_error_response(
        "validation_error",
        "Перевірте введені дані.",
        status.HTTP_400_BAD_REQUEST,
    )
    response.data["fields"] = flatten_error_details(serializer.errors)
    return response


def _build_category_required_response():
    return build_error_response(
        "category_required",
        "Вкажіть категорію продукту.",
        status.HTTP_400_BAD_REQUEST,
    )


def _build_item_not_found_response():
    return build_error_response(
        "item_not_found",
        "Цього продукту вже немає в холодильнику.",
        status.HTTP_404_NOT_FOUND,
    )


def _build_unit_conversion_response(error):
    from_label = ProductUnit(error.from_unit).label
    to_label = ProductUnit(error.to_unit).label
    return build_error_response(
        "unit_not_convertible",
        f"Не вдається перевести {from_label} у {to_label} для цього продукту.",
        status.HTTP_400_BAD_REQUEST,
    )


def _build_quantity_negative_response(item, available):
    unit_label = ProductUnit(item.unit).label
    return build_error_response(
        "quantity_negative",
        f"У холодильнику лише {available.normalize():f} {unit_label}.",
        status.HTTP_400_BAD_REQUEST,
        available=str(available),
    )
