"""Django admin for the product catalog."""

from django.contrib import admin
from django.db.models import Count

from .models import CatalogProduct, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sort_order", "get_product_count")
    ordering = ("sort_order", "name")
    search_fields = ("name", "slug")

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(product_count=Count("products"))

    @admin.display(description="Продуктів", ordering="product_count")
    def get_product_count(self, category):
        return category.product_count


@admin.register(CatalogProduct)
class CatalogProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "default_unit",
        "kcal_per_100g",
        "default_shelf_days",
    )
    list_filter = ("category", "default_unit")
    list_select_related = ("category",)
    ordering = ("name",)
    search_fields = ("name", "aliases")
