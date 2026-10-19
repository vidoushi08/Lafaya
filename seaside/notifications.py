import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.urls import reverse

logger = logging.getLogger(__name__)


def admin_recipients():
    """Active superadmins with an email address."""
    User = get_user_model()
    return sorted(
        set(
            User.objects.filter(is_active=True, is_superuser=True)
            .exclude(email="")
            .values_list("email", flat=True)
        )
    )


def notify_admins_of_booking(booking, request):
    """Email the admins about a new request; never blocks the customer."""
    recipients = admin_recipients()
    if not recipients:
        logger.warning("No admin email to notify about seaside booking %s.", booking.pk)
        return False

    review_url = request.build_absolute_uri(
        reverse("admin:seaside_seasidebookingrequest_change", args=[booking.pk])
    )
    services = ", ".join(service.name for service in booking.services.all()) or "None"
    message = (
        "A new Seaside booking request is awaiting your review.\n\n"
        f"Customer: {booking.first_name} {booking.last_name}\n"
        f"Email: {booking.email}\n"
        f"Phone: {booking.phone}\n"
        f"Event: {booking.event_name or 'Not named'}\n"
        f"Date: {booking.event_date:%d %b %Y}, "
        f"{booking.start_time:%H:%M} to {booking.end_time:%H:%M}\n"
        f"Guests: {booking.expected_guests}\n"
        f"Venue: {booking.venue.name}\n"
        f"Package: {booking.package.name}\n"
        f"Optional services: {services}\n"
        f"Customer budget: Rs {booking.budget:,.2f}\n"
        f"Estimated total: Rs {booking.estimated_total:,.2f}\n\n"
        f"Review, approve or reject it here:\n{review_url}\n"
    )
    try:
        send_mail(
            f"New Seaside booking request: {booking.event_date:%d %b %Y}",
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
        )
    except Exception:
        logger.exception("Could not email admins about seaside booking %s.", booking.pk)
        return False
    return True
