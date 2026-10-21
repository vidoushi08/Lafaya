import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


def generate_booking_reference():
    return f"LAF-{uuid.uuid4().hex[:12].upper()}"


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    source_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        related_name="lafaya_bookings",
    )
    source_object_id = models.PositiveBigIntegerField()
    source_request = GenericForeignKey("source_content_type", "source_object_id")
    reference = models.CharField(
        max_length=16,
        unique=True,
        default=generate_booking_reference,
        editable=False,
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    event_type = models.CharField(max_length=32)
    event_name = models.CharField(max_length=120, blank=True)
    event_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    guests = models.PositiveIntegerField()
    venue_name = models.CharField(max_length=120)
    package_name = models.CharField(max_length=120)
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    estimated_total = models.DecimalField(max_digits=12, decimal_places=2)
    message = models.TextField(blank=True)
    client_name = models.CharField(max_length=301, blank=True)
    client_email = models.EmailField(blank=True)
    client_phone = models.CharField(max_length=32, blank=True)
    services_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=("source_content_type", "source_object_id"),
                name="booking_unique_source_request",
            ),
            models.CheckConstraint(
                condition=models.Q(guests__gte=1),
                name="booking_guests_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(estimated_total__gte=0),
                name="booking_estimated_total_nonnegative",
            ),
        ]

    def __str__(self):
        return f"{self.reference} - {self.event_type} - {self.event_date}"

    def _set_source_status(self, status):
        source = self.source_request
        if source is not None and hasattr(source, "status"):
            source.status = status
            source.save(update_fields=("status",))

    @transaction.atomic
    def approve(self):
        booking = type(self).objects.select_for_update().get(pk=self.pk)
        if booking.status != self.Status.PENDING:
            raise ValidationError("Only pending bookings can be approved.")

        payment = getattr(booking, "payment", None)
        if payment is None or payment.amount <= 0:
            raise ValidationError("Set a positive payment amount before approval.")

        booking.status = self.Status.APPROVED
        booking.save(update_fields=("status", "updated_at"))
        booking._set_source_status(self.Status.APPROVED)
        self.refresh_from_db()
        return self

    @transaction.atomic
    def reject(self):
        booking = type(self).objects.select_for_update().get(pk=self.pk)
        if booking.status != self.Status.PENDING:
            raise ValidationError("Only pending bookings can be rejected.")

        booking.status = self.Status.REJECTED
        booking.save(update_fields=("status", "updated_at"))
        booking._set_source_status(self.Status.REJECTED)
        self.refresh_from_db()
        return self

    @transaction.atomic
    def mark_confirmed(self):
        booking = type(self).objects.select_for_update().get(pk=self.pk)
        if booking.status == self.Status.CONFIRMED:
            return False
        if booking.status != self.Status.APPROVED:
            raise ValidationError("Only approved bookings can be confirmed.")

        payment = getattr(booking, "payment", None)
        if payment is None or payment.status not in ("verified", "demo_paid"):
            raise ValidationError(
                "A booking requires a completed payment before it can be confirmed."
            )

        booking.status = self.Status.CONFIRMED
        booking.confirmed_at = timezone.now()
        booking.save(update_fields=("status", "confirmed_at", "updated_at"))
        self.refresh_from_db()
        return True

    @transaction.atomic
    def mark_completed(self):
        booking = type(self).objects.select_for_update().get(pk=self.pk)
        if booking.status == self.Status.COMPLETED:
            return False
        if booking.status != self.Status.CONFIRMED:
            raise ValidationError("Only confirmed bookings can be completed.")

        booking.status = self.Status.COMPLETED
        booking.completed_at = timezone.now()
        booking.save(update_fields=("status", "completed_at", "updated_at"))
        self.refresh_from_db()
        return True

    @transaction.atomic
    def mark_cancelled(self):
        booking = type(self).objects.select_for_update().get(pk=self.pk)
        if booking.status == self.Status.CANCELLED:
            return False
        if booking.status in (self.Status.REJECTED, self.Status.COMPLETED):
            raise ValidationError("This booking can no longer be cancelled.")

        booking.status = self.Status.CANCELLED
        booking.cancelled_at = timezone.now()
        booking.save(update_fields=("status", "cancelled_at", "updated_at"))
        # A cancelled request no longer holds its venue and date.
        booking._set_source_status(self.Status.CANCELLED)
        self.refresh_from_db()
        return True
