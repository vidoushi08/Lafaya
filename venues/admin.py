from django.contrib import admin

from .models import EventType, Venue


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "price")
    search_fields = ("name", "location")
    list_filter = ("event_types",)
    filter_horizontal = ("event_types",)