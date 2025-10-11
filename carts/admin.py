from django.contrib import admin

from .models import ShippingMethod


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ("name", "base_cost", "is_active", "is_default", "minimum_order_total", "updated_at")
    list_filter = ("is_active", "is_default")
    search_fields = ("name", "description")
    ordering = ("-is_default", "base_cost")
    readonly_fields = ("created_at", "updated_at")
