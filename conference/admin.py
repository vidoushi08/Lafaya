from authentication.admin_site import superadmin_site
from django.contrib import admin
from seaside.admin import PricedCatalogItemAdmin

from .models import (
    ConferenceBookingRequest,
    ConferencePackage,
    ConferenceService,
    ConferenceVenue,
)


class ConferenceVenueAdmin(PricedCatalogItemAdmin):
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


class ConferencePackageAdmin(PricedCatalogItemAdmin):
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


class ConferenceServiceAdmin(PricedCatalogItemAdmin):
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


class ConferenceBookingRequestAdmin(admin.ModelAdmin):
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
        "customer",
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
    fields = ("status", *readonly_fields)

    def has_add_permission(self, request):
        return False


for model, model_admin in (
    (ConferenceVenue, ConferenceVenueAdmin),
    (ConferencePackage, ConferencePackageAdmin),
    (ConferenceService, ConferenceServiceAdmin),
    (ConferenceBookingRequest, ConferenceBookingRequestAdmin),
):
    superadmin_site.register(model, model_admin)
