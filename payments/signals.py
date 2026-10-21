from django.db.models.signals import post_save

from booking.models import Booking

from .models import Payment


def create_payment_for_booking(sender, instance, created, **kwargs):
    if created:
        Payment.objects.create(
            booking=instance,
            amount=instance.estimated_total,
        )


post_save.connect(
    create_payment_for_booking,
    sender=Booking,
    dispatch_uid="payments.create_payment_for_booking",
)
