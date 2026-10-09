from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from common.location import load_city_postal_codes
from .models import User


class CustomerRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "id": "first_name",
                "placeholder": "first name",
                "autocomplete": "given-name",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "id": "last_name",
                "placeholder": "last name",
                "autocomplete": "family-name",
            }
        ),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "id": "email",
                "placeholder": "you@example.com",
                "autocomplete": "email",
            }
        ),
    )
    phone = forms.CharField(
        required=False,
        max_length=32,
        widget=forms.TextInput(
            attrs={
                "id": "phone",
                "placeholder": "+230 5xxx xxxx",
                "autocomplete": "tel",
            }
        ),
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "id": "date_of_birth",
                "type": "date",
                "autocomplete": "bday",
            }
        ),
    )
    gender = forms.ChoiceField(
        choices=[("", "select gender"), *User.Gender.choices],
        widget=forms.Select(attrs={"id": "gender", "autocomplete": "sex"}),
    )
    address = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "id": "address",
                "placeholder": "street address",
                "autocomplete": "street-address",
            }
        ),
    )
    city = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={"id": "city", "autocomplete": "address-level2"}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "phone",
            "date_of_birth",
            "gender",
            "address",
            "city",
        )
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "id": "username",
                    "placeholder": "choose a username",
                    "autocomplete": "username",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.city_postal_codes = load_city_postal_codes()
        self.fields["city"].choices = [
            ("", "select city"),
            *[(city, city) for city in self.city_postal_codes],
        ]
        self.fields["password1"].widget.attrs.update(
            {
                "id": "password1",
                "placeholder": "create a password",
                "autocomplete": "new-password",
            }
        )
        self.fields["password2"].widget.attrs.update(
            {
                "id": "password2",
                "placeholder": "confirm your password",
                "autocomplete": "new-password",
            }
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("an account with this email address already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.account_type = User.AccountType.CUSTOMER
        user.postal_code = self.city_postal_codes.get(user.city, "")
        if commit:
            user.save()
            self.save_m2m()
        return user
