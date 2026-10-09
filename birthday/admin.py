from django.contrib import admin

from .models import BirthdayEnquiry, BirthdayPackage


@admin.register(BirthdayPackage)
class BirthdayPackageAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "package_type", "price", "is_active", "display_order")
    list_filter = ("package_type", "is_active")
    search_fields = ("name", "slug")
    ordering = ("display_order", "name")


@admin.register(BirthdayEnquiry)
class BirthdayEnquiryAdmin(admin.ModelAdmin):
    list_display = ("customer_name", "selected_package", "venue", "status", "quoted_price", "event_date", "created_at")
    list_filter = ("status", "selected_package", "event_date")
    search_fields = ("customer_name", "email", "phone", "notes", "custom_requirements")
    ordering = ("-created_at",)
