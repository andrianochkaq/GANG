"""Cursor pagination for lists that can grow (docs/architecture.md, 5.4)."""

from rest_framework.pagination import CursorPagination


class FridgeItemCursorPagination(CursorPagination):
    ordering = ("name", "id")
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200
