from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from booking.models import Booking
from common.decorators import account_type_required

from .notifications import send_payment_receipt


@account_type_required("customer")
def index(request):
    bookings = (
        Booking.objects.filter(customer=request.user)
        .select_related("payment")
        .order_by("-created_at")
    )
    return render(request, "payments/payment.html", {"bookings": bookings})


@account_type_required("customer")
def payment_detail(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related("payment"),
        pk=booking_id,
        customer=request.user,
    )
    return render(
        request,
        "payments/payment_detail.html",
        {"booking": booking, "payment": booking.payment},
    )


@require_POST
@account_type_required("customer")
def demo_payment(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related("payment"),
        pk=booking_id,
        customer=request.user,
    )
    try:
        completed = booking.payment.complete_demo_payment()
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
    else:
        payment = booking.payment
        receipt_sent = payment.receipt_email_sent_at is not None
        if not receipt_sent and send_payment_receipt(payment):
            payment.receipt_email_sent_at = timezone.now()
            payment.save(update_fields=("receipt_email_sent_at", "updated_at"))
            receipt_sent = True

        if completed and receipt_sent:
            messages.success(
                request,
                "Demo payment complete and receipt email sent. No real card was charged.",
            )
        elif completed:
            messages.error(
                request,
                "Demo payment succeeded, but the receipt email could not be sent. "
                "You can retry sending it below.",
            )
        elif receipt_sent:
            messages.info(request, "This booking has already been paid.")
        else:
            messages.error(
                request,
                "The booking is already paid, but its receipt email could not be "
                "sent. You can retry sending it below.",
            )
    return redirect("payments:payment_detail", booking_id=booking.pk)
