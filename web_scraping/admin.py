from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from web_scraping.models import Marketplace, Product


@admin.register(Marketplace)
class MarketplaceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "base_url",
    )

    list_filter = ("name",)
    search_fields = ("name",)
    search_help_text = (
        "Введите наименование площадки для поиска"
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")
    fields = (
        "name",
        "base_url",
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "marketplace",
        "product_id",
        "url",
        "updated_at",
    )
    list_filter = ("name",)
    search_fields = ("name",)
    search_help_text = (
        "Введите наименование товара для поиска"
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")
    fields = (
        "name",
        "price",
        "marketplace",
        "product_id",
        "url",
        "image_url",
        "updated_at",
    )
