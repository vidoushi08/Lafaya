from datetime import timedelta

from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import MAX_DAYS_AHEAD, ConcertBookingForm, bookable
from .models import ConcertPackage, ConcertService, ConcertVenue
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
                "Only signed-in customers can make a concert booking request."
            )
        form = ConcertBookingForm(request.POST, customer=customer)
        if form.is_valid():
            booking = form.save()
            notify_admins_of_booking(booking, request)
            messages.success(
                request,
                "Your concert booking request has been submitted and is awaiting approval.",
            )
            return redirect(f"{reverse('concert:concert')}#concert-enquiry")
    elif customer is not None:
        form = ConcertBookingForm(
            initial={
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "phone": customer.phone,
            },
            customer=customer,
        )

    return render(
        request,
        "concert/concert.html",
        {
            "venues": ConcertVenue.objects.filter(is_active=True),
            "packages": ConcertPackage.objects.filter(is_active=True),
            "services": ConcertService.objects.filter(is_active=True),
            "bookable_venues": bookable(ConcertVenue),
            "bookable_packages": bookable(ConcertPackage),
            "bookable_services": bookable(ConcertService),
            "form": form,
            "selected_services": (
                form.data.getlist("optional_services")
                if form is not None and form.is_bound
                else []
            ),
            "is_customer": customer is not None,
            "min_event_date": timezone.localdate().isoformat(),
            "max_event_date": (
                timezone.localdate() + timedelta(days=MAX_DAYS_AHEAD)
            ).isoformat(),
            "login_next": f"{reverse('concert:concert')}#concert-enquiry",
        },
    )
