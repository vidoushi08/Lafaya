from django import forms
from django.core.exceptions import ValidationError

from authentication.models import User


class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone",
            "date_of_birth",
            "gender",
            "address",
            "city",
            "postal_code",
        )
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(
            pk=self.instance.pk
        ).exists():
            raise ValidationError(
                "An account with this email address already exists."
            )
        return email
