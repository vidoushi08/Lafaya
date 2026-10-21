from django.contrib import admin, messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.urls import reverse

from authentication.admin_site import superadmin_site
from payments.notifications import send_booking_decision
from payments.models import Payment

from .models import Booking


class BookingRequestAdminActions:
    actions = ("approve_booking_requests", "reject_booking_requests")

    def _apply_booking_decision(self, request, queryset, approve):
        content_type = ContentType.objects.get_for_model(self.model)
        bookings = Booking.objects.filter(
            source_content_type=content_type,
            source_object_id__in=queryset.values("pk"),
        ).select_related("customer", "payment")
        booking_by_request = {booking.source_object_id: booking for booking in bookings}
        changed = 0
        failed_emails = 0

        for booking_request in queryset:
            booking = booking_by_request.get(booking_request.pk)
            if booking is None:
                self.message_user(
                    request,
                    f"Booking request {booking_request.pk} has no linked booking. "
                    "Contact support before changing its status.",
                    level=messages.ERROR,
                )
                continue

            try:
                if approve:
                    booking.approve()
                else:
                    booking.reject()
            except ValidationError as error:
                self.message_user(
                    request,
                    f"{booking.reference}: {' '.join(error.messages)}",
                    level=messages.ERROR,
                )
                continue

            if approve:
                payment_url = request.build_absolute_uri(
                    reverse("payments:payment_detail", args=(booking.pk,))
                )
                delivered = send_booking_decision(booking, True, payment_url)
            else:
                delivered = send_booking_decision(booking, False)

            if not delivered:
                failed_emails += 1
            changed += 1

        decision = "approved" if approve else "rejected"
        if changed:
            self.message_user(
                request,
                f"{changed} booking request(s) {decision}.",
                level=messages.SUCCESS,
            )
        if failed_emails:
            self.message_user(
                request,
                f"{failed_emails} decision email(s) could not be delivered; "
                "the saved booking decisions remain in place.",
                level=messages.ERROR,
            )

    @admin.action(
        description="Approve selected booking requests"
    )
    def approve_booking_requests(self, request, queryset):
        self._apply_booking_decision(request, queryset, approve=True)

    @admin.action(description="Reject selected booking requests")
    def reject_booking_requests(self, request, queryset):
        self._apply_booking_decision(request, queryset, approve=False)


class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0
    can_delete = False
    fields = (
        "amount",
        "currency",
        "status",
        "paid_at",
    )
    readonly_fields = (
        "status",
        "paid_at",
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj is not None and obj.status != Booking.Status.PENDING:
            readonly.extend(("amount", "currency"))
        return readonly


@admin.register(Booking, site=superadmin_site)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "customer",
        "event_type",
        "event_date",
        "venue_name",
        "status",
        "created_at",
    )
    list_filter = ("status", "event_type", "event_date")
    search_fields = ("reference", "customer__email", "event_name", "venue_name")
    readonly_fields = (
        "reference",
        "customer",
        "source_content_type",
        "source_object_id",
        "event_type",
        "event_name",
        "event_date",
        "start_time",
        "end_time",
        "guests",
        "venue_name",
        "package_name",
        "budget",
        "estimated_total",
        "message",
        "created_at",
        "confirmed_at",
        "updated_at",
        "status",
    )
    fields = readonly_fields
    inlines = (PaymentInline,)
    actions = ("approve_bookings", "reject_bookings")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.action(description="Approve selected booking requests")
    def approve_bookings(self, request, queryset):
        approved = 0
        failed_emails = 0
        for booking in queryset:
            try:
                booking.approve()
            except ValidationError as error:
                self.message_user(
                    request,
                    f"{booking.reference}: {' '.join(error.messages)}",
                    level=messages.ERROR,
                )
                continue

            payment_url = request.build_absolute_uri(
                reverse("payments:payment_detail", args=(booking.pk,))
            )
            if not send_booking_decision(booking, True, payment_url):
                failed_emails += 1
            approved += 1

        if approved:
            self.message_user(
                request,
                f"{approved} booking(s) approved.",
                level=messages.SUCCESS,
            )
        if failed_emails:
            self.message_user(
                request,
                f"{failed_emails} approval email(s) could not be delivered; "
                "the saved approvals remain in place.",
                level=messages.ERROR,
            )

    @admin.action(description="Reject selected booking requests")
    def reject_bookings(self, request, queryset):
        rejected = 0
        failed_emails = 0
        for booking in queryset:
            try:
                booking.reject()
            except ValidationError as error:
                self.message_user(
                    request,
                    f"{booking.reference}: {' '.join(error.messages)}",
                    level=messages.ERROR,
                )
                continue
            if not send_booking_decision(booking, False):
                failed_emails += 1
            rejected += 1

        if rejected:
            self.message_user(
                request,
                f"{rejected} booking(s) rejected.",
                level=messages.SUCCESS,
            )
        if failed_emails:
            self.message_user(
                request,
                f"{failed_emails} rejection email(s) could not be delivered; "
                "the saved rejections remain in place.",
                level=messages.ERROR,
            )
