from django.contrib import admin

from authentication.admin_site import superadmin_site
from booking.admin import BookingRequestAdminActions

from .models import (
    WeddingBookingRequest,
    WeddingEnquiry,
    WeddingPackage,
    WeddingService,
    WeddingVenue,
)


@admin.register(WeddingPackage, site=superadmin_site)
class WeddingPackageAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "min_guests", "max_guests", "is_active", "display_order")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("display_order", "name")


@admin.register(WeddingVenue, site=superadmin_site)
class WeddingVenueAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "capacity", "is_active", "position")
    list_filter = ("is_active",)
    search_fields = ("name", "location")
    list_editable = ("capacity", "is_active", "position")


@admin.register(WeddingService, site=superadmin_site)
class WeddingServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "price_basis", "is_active", "position")
    list_filter = ("is_active", "price_basis")
    search_fields = ("name",)
    list_editable = ("price", "price_basis", "is_active", "position")


@admin.register(WeddingBookingRequest, site=superadmin_site)
class WeddingBookingRequestAdmin(BookingRequestAdminActions, admin.ModelAdmin):
    list_display = (
        "event_date", "first_name", "last_name", "venue", "package",
        "expected_guests", "estimated_total", "status", "created_at",
    )
    list_filter = ("status", "event_date")
    search_fields = ("first_name", "last_name", "email", "event_name")
    readonly_fields = (
        "status", "customer", "event_type", "first_name", "last_name", "email",
        "phone", "event_name", "event_date", "start_time", "end_time",
        "expected_guests", "venue", "package", "services", "budget",
        "estimated_total", "price_breakdown", "message", "created_at",
    )
    fields = readonly_fields

    def has_add_permission(self, request):
        return False


@admin.register(WeddingEnquiry, site=superadmin_site)
class WeddingEnquiryAdmin(admin.ModelAdmin):
    list_display = ("customer", "package", "event_date", "status", "quoted_price", "created_at")
    list_filter = ("status", "event_date", "created_at")
    search_fields = ("customer__username", "package__name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
