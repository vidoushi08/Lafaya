from django.contrib import admin

from authentication.admin_site import superadmin_site

from .models import CarEventEnquiry, EventPackage, ExtraService, PackageFeature, Venue


class PackageFeatureInline(admin.TabularInline):
    model = PackageFeature
    extra = 1


class EventPackageAdmin(admin.ModelAdmin):
    list_display = ("name", "tagline", "is_featured", "is_active")
    list_filter = ("is_featured", "is_active")
    search_fields = ("name", "tagline")
    inlines = [PackageFeatureInline]


class VenueAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "location")


class ExtraServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


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
    (CarEventEnquiry, CarEventEnquiryAdmin),
):
    try:
        superadmin_site.register(model, model_admin)
    except admin.sites.AlreadyRegistered:
        pass
