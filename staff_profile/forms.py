from django import forms

from authentication.models import User


class StaffProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "phone",
            "date_of_birth",
            "gender",
            "address",
            "city",
            "postal_code",
        )
        widgets = {
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"autocomplete": "family-name"}),
            "phone": forms.TelInput(attrs={"autocomplete": "tel"}),
            "date_of_birth": forms.DateInput(
                attrs={"type": "date", "autocomplete": "bday"}
            ),
            "gender": forms.Select(attrs={"autocomplete": "sex"}),
            "address": forms.TextInput(attrs={"autocomplete": "street-address"}),
            "city": forms.TextInput(attrs={"autocomplete": "address-level2"}),
            "postal_code": forms.TextInput(attrs={"autocomplete": "postal-code"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["gender"].required = False
