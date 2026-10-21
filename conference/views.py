from datetime import timedelta

from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from seaside.forms import MAX_DAYS_AHEAD, bookable

from .forms import ConferenceBookingForm
from .models import ConferencePackage, ConferenceService, ConferenceVenue
from .notifications import notify_admins_of_booking


def is_customer(user):
    return (
        user.is_authenticated
        and not user.is_superuser
        and user.account_type == user.AccountType.CUSTOMER
    )


def index(request):
    customer = request.user if is_customer(request.user) else None
    form = None

    if request.method == "POST":
        if customer is None:
            return HttpResponseForbidden(
                "Only signed-in customers can make a booking request."
            )
        form = ConferenceBookingForm(request.POST, customer=customer)
        if form.is_valid():
            booking = form.save()
            notify_admins_of_booking(booking, request)
            messages.success(
                request,
                "Your booking request has been submitted and is awaiting approval.",
            )
            return redirect(f"{reverse('conference:conference')}#conference-enquiry")
    elif customer is not None:
        form = ConferenceBookingForm(
            initial={
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "phone": customer.phone,
            },
            customer=customer,
        )

    today = timezone.localdate()
    return render(
        request,
        "conference/conference.html",
        {
            "venues": ConferenceVenue.objects.filter(is_active=True),
            "packages": ConferencePackage.objects.filter(is_active=True),
            "services": ConferenceService.objects.filter(is_active=True),
            "bookable_venues": bookable(ConferenceVenue),
            "bookable_packages": bookable(ConferencePackage),
            "bookable_services": bookable(ConferenceService),
            "form": form,
            "selected_services": (
                form.data.getlist("optional_services")
                if form is not None and form.is_bound
                else []
            ),
            "is_customer": customer is not None,
            "min_event_date": today.isoformat(),
            "max_event_date": (today + timedelta(days=MAX_DAYS_AHEAD)).isoformat(),
            "login_next": f"{reverse('conference:conference')}#conference-enquiry",
        },
    )
