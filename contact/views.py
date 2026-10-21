import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render

from .forms import ContactForm

logger = logging.getLogger(__name__)


def index(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        contact_message = form.save()
        body = (
            f"New contact message #{contact_message.pk}\n\n"
            f"From: {contact_message.name}\n"
            f"Email: {contact_message.email}\n"
            f"Phone: {contact_message.phone or 'Not provided'}\n"
            f"Topic: {contact_message.get_topic_display()}\n"
            f"Subject: {contact_message.subject}\n\n"
            f"{contact_message.message}\n"
        )
        try:
            send_mail(
                f"Contact form: {contact_message.subject}",
                body,
                settings.DEFAULT_FROM_EMAIL,
                [settings.CONTACT_RECIPIENT_EMAIL],
                fail_silently=False,
                reply_to=[contact_message.email],
            )
        except Exception:
            logger.exception("Could not email admins about contact message %s.", contact_message.pk)

        messages.success(
            request,
            "Thanks for contacting Lafaya. Your message has been received, and our team will be in touch.",
        )
        return redirect("contact:contact")

    return render(
        request,
        "contact/contact.html",
        {
            "form": form,
            "contact_email": settings.CONTACT_RECIPIENT_EMAIL,
            "contact_phone": "+230 5123 4567",
            "contact_address": "University of Mauritius, Réduit 80837, Mauritius",
        },
    )
