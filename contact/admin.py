from django.contrib import admin

from authentication.admin_site import superadmin_site

from .models import ContactMessage


@admin.register(ContactMessage, site=superadmin_site)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "email", "topic", "status", "created_at")
    list_filter = ("status", "topic", "created_at")
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("name", "email", "phone", "topic", "subject", "message", "created_at", "updated_at")
    fields = readonly_fields + ("status",)
    actions = ("mark_read", "mark_replied", "close_messages")

    @admin.action(description="Mark selected messages as read")
    def mark_read(self, request, queryset):
        queryset.update(status=ContactMessage.Status.READ)

    @admin.action(description="Mark selected messages as replied")
    def mark_replied(self, request, queryset):
        queryset.update(status=ContactMessage.Status.REPLIED)

    @admin.action(description="Close selected messages")
    def close_messages(self, request, queryset):
        queryset.update(status=ContactMessage.Status.CLOSED)
