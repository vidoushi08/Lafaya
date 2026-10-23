from datetime import datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django import forms
from django.db import transaction
from django.utils import timezone

from .models import WeddingBookingRequest, WeddingEnquiry, WeddingPackage, WeddingService, WeddingVenue

MAX_BUDGET = Decimal("10000000")
MAX_GUESTS = 10000
MAX_DAYS_AHEAD = 730
MAX_DURATION = timedelta(hours=5)
LATEST_END = time(3, 0)


def booking_window(event_date, start, end):
    begin = datetime.combine(event_date, start)
    finish = datetime.combine(event_date, end)
    if end <= start:
        finish += timedelta(days=1)
    return begin, finish


def clashing_booking(venue, event_date):
    return WeddingBookingRequest.objects.filter(
        venue=venue,
        event_date=event_date,
        status__in=(
            WeddingBookingRequest.Status.PENDING,
            WeddingBookingRequest.Status.APPROVED,
        ),
    ).first()


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
        min_value=Decimal("0.01"),
        max_value=MAX_BUDGET,
        max_digits=12,
        decimal_places=2,
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
        if self.phone_locked:
            return self.customer.phone
        return self.cleaned_data["phone"].strip()

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
        guests = cleaned.get("expected_guests")
        venue = cleaned.get("venue")
        package = cleaned.get("package")

        if start and end and start == end:
            self.add_error("end_time", "The end time must differ from the start time.")
        elif event_date and start and end:
            begin, finish = booking_window(event_date, start, end)
            cutoff = datetime.combine(begin.date(), LATEST_END)
            if begin.time() >= LATEST_END:
                cutoff += timedelta(days=1)
            if finish - begin > MAX_DURATION:
                self.add_error("end_time", "An event can last 5 hours at most.")
            elif finish > cutoff:
                self.add_error("end_time", "The event must be over by 3:00 am.")

        if (
            event_date
            and start
            and event_date == timezone.localdate()
            and start <= timezone.localtime().time()
        ):
            self.add_error("start_time", "The start time must still be in the future.")

        if event_date and venue:
            clash = clashing_booking(venue, event_date)
            if clash:
                self.add_error(
                    "venue",
                    f"{venue.name} already has a wedding request on "
                    f"{event_date:%d %b %Y}. Please choose another date or venue.",
                )

        if guests and venue and venue.capacity and guests > venue.capacity:
            self.add_error("venue", f"{venue.name} holds up to {venue.capacity} guests.")
        if guests and package:
            if guests < package.min_guests:
                self.add_error("package", f"{package.name} needs at least {package.min_guests} guests.")
            elif package.max_guests and guests > package.max_guests:
                self.add_error("package", f"{package.name} accommodates up to {package.max_guests} guests.")

        budget = cleaned.get("budget")
        if guests and package and budget is not None:
            services = list(cleaned.get("optional_services") or [])
            total = package.price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            lines = [{
                "kind": "package",
                "name": package.name,
                "unit_price": str(package.price),
                "price_basis": "per_booking",
                "quantity": 1,
                "subtotal": str(total),
            }]
            for service in services:
                quantity = guests if service.price_basis == WeddingService.PriceBasis.PER_GUEST else 1
                subtotal = (service.price * quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                total += subtotal
                lines.append({
                    "kind": "service",
                    "name": service.name,
                    "unit_price": str(service.price),
                    "price_basis": service.price_basis,
                    "quantity": quantity,
                    "subtotal": str(subtotal),
                })
            if total > budget:
                self.add_error(
                    "budget",
                    f"Your selection costs Rs {total:,.2f}, above your budget of Rs {budget:,.2f}.",
                )
            self.estimate = (total, lines, services)
        return cleaned

    @transaction.atomic
    def save(self):
        data = self.cleaned_data
        total, lines, services = self.estimate
        request = WeddingBookingRequest.objects.create(
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
        request.services.set(services)
        return request


class WeddingEnquiryForm(forms.ModelForm):
    class Meta:
        model = WeddingEnquiry
        fields = ["event_date", "venue", "custom_requirements", "notes"]
        widgets = {
            "event_date": forms.DateInput(attrs={"type": "date"}),
            "venue": forms.TextInput(attrs={"placeholder": "Preferred venue"}),
            "custom_requirements": forms.Textarea(
                attrs={"placeholder": "Tell us about your wedding plans...", "rows": 4}
            ),
            "notes": forms.Textarea(
                attrs={"placeholder": "Any other information...", "rows": 3}
            ),
        }
