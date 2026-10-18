from django import forms
from django.utils import timezone

from .models import CarEventEnquiry, EventPackage, ExtraService, Venue


class CarEventEnquiryForm(forms.ModelForm):
    class Meta:
        model = CarEventEnquiry
        fields = [
            "full_name",
            "email",
            "phone",
            "preferred_date",
            "expected_attendees",
            "venue",
            "event_package",
            "extras",
            "message",
        ]
        widgets = {
            "preferred_date": forms.DateInput(attrs={"type": "date"}),
            "extras": forms.CheckboxSelectMultiple(),
            "message": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Tell us about your event"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["venue"].queryset = Venue.objects.filter(is_active=True)
        self.fields["event_package"].queryset = EventPackage.objects.filter(
            is_active=True
        )
        self.fields["extras"].queryset = ExtraService.objects.filter(is_active=True)
        self.fields["preferred_date"].widget.attrs["min"] = (
            timezone.localdate().isoformat()
        )
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs.setdefault("class", "car-events-form-control")

    def clean_preferred_date(self):
        selected_date = self.cleaned_data["preferred_date"]
        if selected_date < timezone.localdate():
            raise forms.ValidationError("Please choose today or a future date.")
        return selected_date
