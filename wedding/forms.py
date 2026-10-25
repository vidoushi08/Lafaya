from datetime import timedelta
from decimal import Decimal

from django import forms
from django.db import transaction
from django.utils import timezone

from .models import (
    WeddingBookingRequest,
    WeddingPackage,
    WeddingService,
    WeddingVenue,
)

MAX_BUDGET = Decimal("10000000")
MAX_GUESTS = 10000
MAX_DAYS_AHEAD = 730


class WeddingBookingForm(forms.Form):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    phone = forms.CharField(max_length=32)
    event_name = forms.CharField(max_length=120, required=False)
    event_date = forms.DateField()
    start_time = forms.TimeField()
    end_time = forms.TimeField()
    expected_guests = forms.IntegerField(min_value=1, max_value=MAX_GUESTS)
    venue = forms.ModelChoiceField(queryset=WeddingVenue.objects.none())
    package = forms.ModelChoiceField(queryset=WeddingPackage.objects.none())
    optional_services = forms.ModelMultipleChoiceField(
        queryset=WeddingService.objects.none(), required=False
    )
    budget = forms.DecimalField(
        min_value=Decimal("0.01"), max_value=MAX_BUDGET,
        max_digits=12, decimal_places=2,
    )
    message = forms.CharField(max_length=1000, required=False)

    def __init__(self, *args, customer, **kwargs):
        super().__init__(*args, **kwargs)
        self.customer = customer
        self.fields["venue"].queryset = WeddingVenue.objects.filter(is_active=True)
        self.fields["package"].queryset = WeddingPackage.objects.filter(is_active=True)
        self.fields["optional_services"].queryset = WeddingService.objects.filter(
            is_active=True, price__isnull=False
        )

    @property
    def phone_locked(self):
        return bool(self.customer.phone)

    def clean_phone(self):
        return self.customer.phone if self.phone_locked else self.cleaned_data["phone"].strip()

    def clean_event_date(self):
        event_date = self.cleaned_data["event_date"]
        today = timezone.localdate()
        if event_date < today:
            raise forms.ValidationError("The event date cannot be in the past.")
        if event_date > today + timedelta(days=MAX_DAYS_AHEAD):
            raise forms.ValidationError("Please choose a date within the next two years.")
        return event_date

    def clean(self):
        cleaned = super().clean()
        event_date = cleaned.get("event_date")
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")
        if start and end and start == end:
            self.add_error("end_time", "The end time must differ from the start time.")
        if event_date and start and event_date == timezone.localdate():
            if start <= timezone.localtime().time():
                self.add_error("start_time", "The start time must still be in the future.")

        venue = cleaned.get("venue")
        package = cleaned.get("package")
        guests = cleaned.get("expected_guests")
        if event_date and venue and WeddingBookingRequest.objects.filter(
            venue=venue,
            event_date=event_date,
            status__in=(WeddingBookingRequest.Status.PENDING, WeddingBookingRequest.Status.APPROVED),
        ).exists():
            self.add_error("venue", "This venue already has an active booking request for that date.")
        if guests and venue and venue.capacity and guests > venue.capacity:
            self.add_error("venue", f"{venue.name} holds up to {venue.capacity} guests.")
        if guests and package:
            if guests < package.min_guests:
                self.add_error("package", f"{package.name} needs at least {package.min_guests} guests.")
            elif package.max_guests and guests > package.max_guests:
                self.add_error("package", f"{package.name} accommodates up to {package.max_guests} guests.")

        budget = cleaned.get("budget")
        if package and budget is not None:
            services = list(cleaned.get("optional_services") or [])
            total = package.price + sum(
                (service.price for service in services), Decimal("0.00")
            )
            if total > budget:
                self.add_error("budget", f"Your selection costs Rs {total:,.2f}, above your budget of Rs {budget:,.2f}.")
            self.estimate = (total, services)
        return cleaned

    @transaction.atomic
    def save(self):
        data = self.cleaned_data
        total, services = self.estimate
        breakdown = [{"name": data["package"].name, "unit_price": str(data["package"].price), "subtotal": str(data["package"].price)}]
        breakdown.extend(
            {"name": service.name, "unit_price": str(service.price), "subtotal": str(service.price)}
            for service in services
        )
        booking = WeddingBookingRequest.objects.create(
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
            price_breakdown=breakdown,
            message=data["message"].strip(),
        )
        booking.services.set(services)
        return booking
