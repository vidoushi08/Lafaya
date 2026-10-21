from datetime import datetime, time, timedelta
from decimal import Decimal

from django import forms
from django.db import transaction
from django.utils import timezone

from seaside.forms import (
    MAX_BUDGET,
    MAX_DAYS_AHEAD,
    MAX_GUESTS,
    booking_window,
    bookable,
)
from seaside.pricing import calculate_estimate

from .models import (
    ConferenceBookingRequest,
    ConferencePackage,
    ConferenceService,
    ConferenceVenue,
)

MAX_DURATION = timedelta(hours=6)
LATEST_END = time(23, 59)


def clashing_booking(venue, event_date, start, end):
    """An active request for this venue whose time overlaps the given one."""
    begin, finish = booking_window(event_date, start, end)
    nearby = ConferenceBookingRequest.objects.filter(
        venue=venue,
        status__in=(
            ConferenceBookingRequest.Status.PENDING,
            ConferenceBookingRequest.Status.APPROVED,
        ),
        event_date__range=(
            event_date - timedelta(days=1),
            event_date + timedelta(days=1),
        ),
    )
    for other in nearby:
        if other.event_date == event_date:
            return other
        other_begin, other_finish = booking_window(
            other.event_date, other.start_time, other.end_time
        )
        if begin < other_finish and finish > other_begin:
            return other
    return None


class ConferenceBookingForm(forms.Form):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    phone = forms.CharField(max_length=32)
    event_name = forms.CharField(max_length=120, required=False)
    event_date = forms.DateField()
    start_time = forms.TimeField()
    end_time = forms.TimeField()
    expected_guests = forms.IntegerField(min_value=1, max_value=MAX_GUESTS)
    venue = forms.ModelChoiceField(queryset=ConferenceVenue.objects.none())
    package = forms.ModelChoiceField(queryset=ConferencePackage.objects.none())
    optional_services = forms.ModelMultipleChoiceField(
        queryset=ConferenceService.objects.none(),
        required=False,
    )
    budget = forms.DecimalField(
        min_value=Decimal("0.01"),
        max_value=MAX_BUDGET,
        max_digits=12,
        decimal_places=2,
    )
    message = forms.CharField(max_length=1000, required=False)

    def __init__(self, *args, customer, **kwargs):
        super().__init__(*args, **kwargs)
        self.customer = customer
        self.fields["venue"].queryset = bookable(ConferenceVenue)
        self.fields["package"].queryset = bookable(ConferencePackage)
        self.fields["optional_services"].queryset = bookable(ConferenceService)

    @property
    def phone_locked(self):
        return bool(self.customer.phone)

    def clean_phone(self):
        # The account phone number is authoritative when one exists.
        if self.phone_locked:
            return self.customer.phone
        return self.cleaned_data["phone"].strip()

    def clean_event_date(self):
        event_date = self.cleaned_data["event_date"]
        today = timezone.localdate()
        if event_date < today:
            raise forms.ValidationError("The event date cannot be in the past.")
        if event_date > today + timedelta(days=MAX_DAYS_AHEAD):
            raise forms.ValidationError(
                "Please choose a date within the next two years."
            )
        return event_date

    def clean(self):
        cleaned = super().clean()
        event_date = cleaned.get("event_date")
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")

        if start and end and end == start:
            self.add_error("end_time", "The end time must differ from the start time.")
        elif event_date and start and end:
            begin, finish = booking_window(event_date, start, end)
            if finish - begin > MAX_DURATION:
                self.add_error("end_time", "A conference can last 6 hours at most.")
            elif finish > datetime.combine(begin.date(), LATEST_END):
                self.add_error("end_time", "The conference must be over by midnight.")
        if (
            event_date
            and start
            and event_date == timezone.localdate()
            and start <= timezone.localtime().time()
        ):
            self.add_error("start_time", "The start time must still be in the future.")

        venue = cleaned.get("venue")
        if event_date and start and end and end != start and venue:
            clash = clashing_booking(venue, event_date, start, end)
            if clash is not None:
                self.add_error(
                    "venue",
                    f"{venue.name} already has an event request on "
                    f"{clash.event_date:%d %b %Y} ({clash.start_time:%H:%M} to "
                    f"{clash.end_time:%H:%M}). Only one event per venue is "
                    "allowed at a time, so please choose another date or venue.",
                )
        package = cleaned.get("package")
        guests = cleaned.get("expected_guests")
        if guests and venue and venue.capacity and guests > venue.capacity:
            self.add_error(
                "venue",
                f"{venue.name} holds up to {venue.capacity} attendees.",
            )
        if guests and package:
            if guests < package.min_guests:
                self.add_error(
                    "package",
                    f"{package.name} needs at least {package.min_guests} attendees.",
                )
            elif package.max_guests and guests > package.max_guests:
                self.add_error(
                    "package",
                    f"{package.name} accommodates up to {package.max_guests} attendees.",
                )

        budget = cleaned.get("budget")
        if guests and venue and package and budget is not None:
            services = list(cleaned.get("optional_services") or [])
            total, lines = calculate_estimate(venue, package, services, guests)
            if total > budget:
                self.add_error(
                    "budget",
                    f"Your selection costs Rs {total:,.2f}, which is above your "
                    f"budget of Rs {budget:,.2f}.",
                )
            self.estimate = (total, lines, services)
        return cleaned

    @transaction.atomic
    def save(self):
        data = self.cleaned_data
        total, lines, services = self.estimate
        booking = ConferenceBookingRequest.objects.create(
            customer=self.customer,
            first_name=data["first_name"].strip(),
            last_name=data["last_name"].strip(),
            email=self.customer.email,
            phone=data["phone"],
            event_name=data["event_name"].strip(),
            event_date=data["event_date"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            expected_guests=data["expected_guests"],
            venue=data["venue"],
            package=data["package"],
            budget=data["budget"],
            estimated_total=total,
            price_breakdown=lines,
            message=data["message"].strip(),
        )
        booking.services.set(services)
        return booking
