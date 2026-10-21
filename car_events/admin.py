from django.contrib import admin
from django.templatetags.static import static
from django.utils.html import format_html

from authentication.admin_site import superadmin_site
from booking.admin import BookingRequestAdminActions

from .models import (
    CarEventBookingRequest,
    CarEventEnquiry,
    EventPackage,
    ExtraService,
    PackageFeature,
    Venue,
)


class PackageFeatureInline(admin.TabularInline):
    model = PackageFeature
    extra = 1


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


class VenueAdmin(PricedCatalogItemAdmin):
    list_display = (
        "name",
        "location",
        "min_attendees",
        "max_attendees",
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
        "min_attendees",
        "max_attendees",
        "price",
        "price_basis",
        "is_active",
        "position",
    )


class EventPackageAdmin(PricedCatalogItemAdmin):
    list_display = (
        "name",
        "tagline",
        "min_attendees",
        "max_attendees",
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
        "image_preview",
        "uploaded_image",
        "min_attendees",
        "max_attendees",
        "price",
        "price_basis",
        "is_featured",
        "is_active",
        "position",
    )
    inlines = [PackageFeatureInline]


class ExtraServiceAdmin(PricedCatalogItemAdmin):
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


class CarEventBookingRequestAdmin(BookingRequestAdminActions, admin.ModelAdmin):
    list_display = (
        "event_date",
        "first_name",
        "last_name",
        "venue",
        "package",
        "expected_attendees",
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
        "expected_attendees",
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


class CarEventEnquiryAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "email",
        "preferred_date",
        "venue",
        "event_package",
        "status",
        "created_at",
    )
    list_filter = ("status", "preferred_date", "venue", "event_package")
    search_fields = ("full_name", "email", "phone")
    filter_horizontal = ("extras",)
    readonly_fields = ("created_at", "updated_at")


for model, model_admin in (
    (Venue, VenueAdmin),
    (EventPackage, EventPackageAdmin),
    (ExtraService, ExtraServiceAdmin),
    (CarEventBookingRequest, CarEventBookingRequestAdmin),
    (CarEventEnquiry, CarEventEnquiryAdmin),
):
    try:
        superadmin_site.register(model, model_admin)
    except admin.sites.AlreadyRegistered:
        pass
