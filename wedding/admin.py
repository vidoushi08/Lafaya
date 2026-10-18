from django.contrib import admin
from .models import WeddingPackage, WeddingEnquiry

#allos managing wedding packages through Django admin
@admin.register(WeddingPackage)
class WeddingPackageAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "is_active", "display_order")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("display_order", "name")


@admin.register(WeddingEnquiry)
class WeddingEnquiryAdmin(admin.ModelAdmin):
    list_display = (
        "customer",
        "package",
        "event_date",
        "status",
        "quoted_price",
        "created_at",
    )

    list_filter = ("status", "event_date", "created_at")
    search_fields = ("customer__username", "package__name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)