import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_booking_decision(booking, approved, payment_url=""):
    recipient = booking.customer.email
    if not recipient:
        logger.warning(
            "Cannot send booking decision for %s: customer has no email.",
            booking.reference,
        )
        return False

    if approved:
        subject = f"Lafaya booking approved: {booking.reference}"
        message = (
            f"Your {booking.event_type} booking request ({booking.reference}) "
            "has been approved.\n\n"
            f"Amount due: {booking.payment.currency} "
            f"{booking.payment.amount:,.2f}\n\n"
            "You can continue to the credit/debit card demo payment here:\n"
            f"{payment_url}\n\n"
            "This is a demo only. It does not charge a real card or require "
            "card details."
        )
    else:
        subject = f"Lafaya booking request update: {booking.reference}"
        message = (
            f"Your {booking.event_type} booking request ({booking.reference}) "
            "could not be approved. Please contact Lafaya if you need further "
            "information."
        )

    try:
        sent_count = send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            "Could not send %s decision email for booking %s.",
            "approval" if approved else "rejection",
            booking.reference,
        )
        return False

    if sent_count != 1:
        logger.error(
            "Booking decision email for %s was not accepted by the email backend.",
            booking.reference,
        )
        return False
    return True


def send_payment_receipt(payment):
    booking = payment.booking
    recipient = booking.customer.email
    if not recipient:
        logger.warning(
            "Cannot send payment receipt for booking %s: customer has no email.",
            booking.reference,
        )
        return False

    subject = f"Lafaya payment successful: {booking.reference}"
    message = (
        f"Hello {booking.customer.first_name or booking.customer.username},\n\n"
        "Your demo payment was successful and your booking is confirmed.\n\n"
        f"Booking reference: {booking.reference}\n"
        f"Event: {booking.event_type}"
        f"{f' - {booking.event_name}' if booking.event_name else ''}\n"
        f"Event date: {booking.event_date:%d %b %Y}\n"
        f"Amount: {payment.currency} {payment.amount:,.2f}\n"
        f"Payment date: {payment.paid_at:%d %b %Y %H:%M}\n\n"
        "This was a demo payment only. No real card was charged. "
        "Your card details were not sent to or stored by Lafaya."
    )

    try:
        sent_count = send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            "Could not send payment receipt for booking %s.",
            booking.reference,
        )
        return False

    if sent_count != 1:
        logger.error(
            "Payment receipt for booking %s was not accepted by the email backend.",
            booking.reference,
        )
        return False
    return True
