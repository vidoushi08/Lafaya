from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class Payment(models.Model):
    class Status(models.TextChoices):
        AWAITING_PAYMENT = "awaiting_payment", "Awaiting payment"
        VERIFIED = "verified", "Verified"
        DEMO_PAID = "demo_paid", "Paid (demo)"

    booking = models.OneToOneField(
        "booking.Booking",
        on_delete=models.PROTECT,
        related_name="payment",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="MUR")
    instructions = models.TextField(
        blank=True,
        help_text="Manual payment instructions shown to the customer after approval.",
    )
    status = models.CharField(
        max_length=24,
        choices=Status.choices,
        default=Status.AWAITING_PAYMENT,
    )
    transaction_reference = models.CharField(max_length=128, blank=True)
    reference_submitted_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_payments",
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    receipt_email_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gte=0),
                name="payment_amount_nonnegative",
            ),
        ]

    def __str__(self):
        return f"{self.booking.reference} - {self.get_status_display()}"

    @transaction.atomic
    def complete_demo_payment(self):
        payment = type(self).objects.select_for_update().select_related(
            "booking"
        ).get(pk=self.pk)
        if payment.booking.status in (
            payment.booking.Status.REJECTED,
            payment.booking.Status.CANCELLED,
        ):
            raise ValidationError("This booking cannot be paid.")
        if payment.status in (self.Status.VERIFIED, self.Status.DEMO_PAID):
            return False
        if payment.booking.status != payment.booking.Status.APPROVED:
            raise ValidationError("Only approved bookings can be paid.")
        if payment.amount <= 0:
            raise ValidationError("The payment amount must be positive.")

        payment.status = self.Status.DEMO_PAID
        payment.paid_at = timezone.now()
        payment.save(update_fields=("status", "paid_at", "updated_at"))
        payment.booking.mark_confirmed()
        self.refresh_from_db()
        return True
