from django.contrib import admin

from authentication.admin_site import superadmin_site

from .models import Payment


@admin.register(Payment, site=superadmin_site)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "booking",
        "amount",
        "currency",
        "status",
        "paid_at",
    )
    list_filter = ("status", "currency")
    search_fields = ("booking__reference",)
    readonly_fields = (
        "booking",
        "status",
        "paid_at",
        "created_at",
        "updated_at",
    )
    fields = (
        "booking",
        "amount",
        "currency",
        "status",
        "paid_at",
        "created_at",
        "updated_at",
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj is not None and obj.booking.status != obj.booking.Status.PENDING:
            readonly.extend(("amount", "currency"))
        return readonly

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
