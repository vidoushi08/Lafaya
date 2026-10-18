from django import forms
from .models import WeddingEnquiry


class WeddingEnquiryForm(forms.ModelForm):

    class Meta:
        model = WeddingEnquiry
        fields = [
            "event_date",
            "venue",
            "custom_requirements",
            "notes",
        ]

        widgets = {
            "event_date": forms.DateInput(
                attrs={"type": "date"}
            ),
            "venue": forms.TextInput(
                attrs={
                    "placeholder": "Preferred venue"
                }
            ),
            "custom_requirements": forms.Textarea(
                attrs={
                    "placeholder": "Tell us about your wedding plans...",
                    "rows": 4,
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "placeholder": "Any other information...",
                    "rows": 3,
                }
            ),
        }