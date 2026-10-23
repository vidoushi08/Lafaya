from django.contrib import admin

from authentication.admin_site import superadmin_site

from .models import Review


@admin.register(Review, site=superadmin_site)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("customer", "booking", "rating", "status", "created_at")
    list_filter = ("status", "rating", "created_at")
    search_fields = ("customer__email", "booking__reference", "comment")
    readonly_fields = ("customer", "booking", "rating", "comment", "created_at", "updated_at")
    fields = ("customer", "booking", "rating", "comment", "status", "created_at", "updated_at")
    actions = ("publish_reviews", "reject_reviews")

    @admin.action(description="Publish selected reviews")
    def publish_reviews(self, request, queryset):
        queryset.update(status=Review.Status.PUBLISHED)

    @admin.action(description="Reject selected reviews")
    def reject_reviews(self, request, queryset):
        queryset.update(status=Review.Status.REJECTED)
