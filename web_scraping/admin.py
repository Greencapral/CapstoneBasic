from django.contrib import admin

from web_scraping.models import Marketplace, Product, Searchers


@admin.register(Marketplace)
class MarketplaceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "base_url",
    )

    list_filter = ("name",)
    search_fields = ("name",)
    search_help_text = "Введите наименование площадки для поиска"
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
    search_help_text = "Введите наименование товара для поиска"
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

@admin.register(Searchers)
class SearchersAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "query",
        "get_products",
        "get_marketplaces",
        "updated_at",

    )

    def get_products(self, obj):
        """Возвращает список продуктов через запятую."""
        return ", ".join([product.name for product in obj.products.all()])
    get_products.short_description = "Продукты"  # Заголовок колонки

    def get_marketplaces(self, obj):
        """Возвращает список маркетплейсов через запятую."""
        return ", ".join([marketplace.name for marketplace in obj.marketplaces.all()])
    get_marketplaces.short_description = "Маркетплейсы"  # Заголовок колонки

    list_filter = ("user", "products",)
    search_fields = ("user",)
    search_help_text = "Введите имя пользователя для поиска"
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")
    fields = (
        "user",
        "query",
        "products",
        "marketplaces",
    )