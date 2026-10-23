from django import forms
from django.utils import timezone

from booking.models import Booking

from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("booking", "rating", "comment")
        widgets = {
            "booking": forms.Select(attrs={"class": "reviews-booking-select"}),
            "rating": forms.HiddenInput(),
            "comment": forms.Textarea(
                attrs={
                    "rows": 5,
                    "maxlength": 2000,
                    "placeholder": "What did you love about your event? Share your experience...",
                }
            ),
        }

    def __init__(self, *args, customer, **kwargs):
        super().__init__(*args, **kwargs)
        self.customer = customer
        reviewed_bookings = Review.objects.values_list("booking_id", flat=True)
        self.fields["booking"].queryset = Booking.objects.filter(
            customer=customer,
            status=Booking.Status.CONFIRMED,
            event_date__lt=timezone.localdate(),
        ).exclude(pk__in=reviewed_bookings).order_by("-event_date")
        self.fields["booking"].label = "Event to review"

    def clean_booking(self):
        booking = self.cleaned_data["booking"]
        if booking.customer_id != self.customer.pk:
            raise forms.ValidationError("Choose one of your own bookings.")
        if booking.status != Booking.Status.CONFIRMED or booking.event_date >= timezone.localdate():
            raise forms.ValidationError("You can review an event after it has taken place.")
        if Review.objects.filter(booking=booking).exists():
            raise forms.ValidationError("You have already reviewed this event.")
        return booking

    def save(self, commit=True):
        review = super().save(commit=False)
        review.customer = self.customer
        if commit:
            review.save()
        return review
