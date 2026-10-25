from django.contrib import admin
from django.templatetags.static import static
from django.utils.html import format_html

from authentication.admin_site import superadmin_site
from booking.admin import BookingRequestAdminActions

from .models import (
    ConcertBookingRequest,
    ConcertPackage,
    ConcertService,
    ConcertVenue,
)


class PricedCatalogItemAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "price_basis", "is_active", "position")
    list_editable = ("price", "price_basis", "is_active", "position")
    list_filter = ("is_active", "price_basis")
    search_fields = ("name",)
    readonly_fields = ("image_preview",)

    @admin.display(description="Current image")
    def image_preview(self, obj):
        if obj.uploaded_image:
            return format_html(
                '<img src="{}" alt="" style="max-width: 240px; max-height: 160px;">',
                obj.uploaded_image.url,
            )
        if obj.image:
            return format_html(
                '<img src="{}" alt="" style="max-width: 240px; max-height: 160px;">',
                static(obj.image),
            )
        return "No image uploaded"


class ConcertVenueAdmin(PricedCatalogItemAdmin):
    list_display = (
        "name",
        "location",
        "capacity",
        "price",
        "price_basis",
        "is_active",
        "position",
        "image_preview",
    )
    search_fields = ("name", "location")
    fields = (
        "name",
        "location",
        "description",
        "image",
        "image_preview",
        "uploaded_image",
        "capacity",
        "price",
        "price_basis",
        "is_active",
        "position",
    )


class ConcertPackageAdmin(PricedCatalogItemAdmin):
    list_display = (
        "name",
        "tagline",
        "min_guests",
        "max_guests",
        "price",
        "price_basis",
        "is_featured",
        "is_active",
        "position",
        "image_preview",
    )
    list_editable = ("price", "price_basis", "is_featured", "is_active", "position")
    fields = (
        "name",
        "tagline",
        "description",
        "image",
        "features",
        "image_preview",
        "uploaded_image",
        "min_guests",
        "max_guests",
        "price",
        "price_basis",
        "is_featured",
        "is_active",
        "position",
    )


class ConcertServiceAdmin(PricedCatalogItemAdmin):
    list_display = (
        "name",
        "price",
        "price_basis",
        "is_active",
        "position",
        "image_preview",
    )
    fields = (
        "name",
        "description",
        "highlights",
        "image",
        "image_preview",
        "uploaded_image",
        "price",
        "price_basis",
        "is_active",
        "position",
    )


class ConcertBookingRequestAdmin(BookingRequestAdminActions, admin.ModelAdmin):
    list_display = (
        "event_date",
        "first_name",
        "last_name",
        "venue",
        "package",
        "expected_guests",
        "estimated_total",
        "status",
        "created_at",
    )
    list_filter = ("status", "event_date")
    search_fields = ("first_name", "last_name", "email", "event_name")
    readonly_fields = (
        "status",
        "customer",
        "event_type",
        "first_name",
        "last_name",
        "email",
        "phone",
        "event_name",
        "event_date",
        "start_time",
        "end_time",
        "expected_guests",
        "venue",
        "package",
        "services",
        "budget",
        "estimated_total",
        "price_breakdown",
        "message",
        "created_at",
    )
    fields = readonly_fields

    def has_add_permission(self, request):
        return False


for model, model_admin in (
    (ConcertVenue, ConcertVenueAdmin),
    (ConcertPackage, ConcertPackageAdmin),
    (ConcertService, ConcertServiceAdmin),
    (ConcertBookingRequest, ConcertBookingRequestAdmin),
):
    superadmin_site.register(model, model_admin)
