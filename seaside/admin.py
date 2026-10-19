from django.contrib import admin
from django.templatetags.static import static
from django.utils.html import format_html

from authentication.admin_site import superadmin_site

from .models import SeasidePackage, SeasideService, SeasideVenue


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
        static_image = getattr(obj, "image", "")
        if static_image:
            return format_html(
                '<img src="{}" alt="" style="max-width: 240px; max-height: 160px;">',
                static(static_image),
            )
        return "No image uploaded"


class SeasideVenueAdmin(PricedCatalogItemAdmin):
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


class SeasidePackageAdmin(PricedCatalogItemAdmin):
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


class SeasideServiceAdmin(PricedCatalogItemAdmin):
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


for model, model_admin in (
    (SeasideVenue, SeasideVenueAdmin),
    (SeasidePackage, SeasidePackageAdmin),
    (SeasideService, SeasideServiceAdmin),
):
    superadmin_site.register(model, model_admin)
