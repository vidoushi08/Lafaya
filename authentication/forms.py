import logging

from django import forms
from django.contrib.auth import authenticate
from django.conf import settings
from django.contrib.auth.forms import (
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils import timezone

from common.location import load_city_postal_codes
from .models import User


logger = logging.getLogger(__name__)


class CaseInsensitivePasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        active_users = User.objects.filter(email__iexact=email, is_active=True)
        return (user for user in active_users if user.has_usable_password())

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        if settings.DEBUG:
            logger.warning(
                "Password reset email generated (token_length=%d)",
                len(context["token"]),
            )
        return super().send_mail(
            subject_template_name,
            email_template_name,
            context,
            from_email,
            to_email,
            html_email_template_name,
        )


class EmailLoginForm(forms.Form):
    identifier = forms.CharField(
        label="Email address or username",
        max_length=254,
        strip=True,
        widget=forms.TextInput(
            attrs={
                "id": "identifier",
                "placeholder": "email address or username",
                "autocomplete": "username",
                "required": True,
            }
        ),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "id": "password",
                "placeholder": "enter your password",
                "autocomplete": "current-password",
                "required": True,
            }
        ),
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        identifier = cleaned_data.get("identifier")
        password = cleaned_data.get("password")
        if identifier and password:
            self.user_cache = authenticate(
                self.request,
                username=identifier,
                password=password,
            )
            if self.user_cache is None:
                raise ValidationError("Invalid email/username or password.")
        return cleaned_data

    def get_user(self):
        return self.user_cache


class PasswordResetTrackingSetPasswordForm(SetPasswordForm):
    def save(self, commit=True):
        user = super().save(commit=False)
        user.password_reset_at = timezone.now()
        if commit:
            user.save()
            send_mail(
                "Your Lafaya password was changed",
                "The password for your Lafaya account was changed. "
                "If you did not make this change, contact the Lafaya team.",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            )
        return user


class EmailAddressForm(forms.Form):
    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": "you@example.com",
                "required": True,
            }
        ),
    )


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
        user.is_active = False
        user.postal_code = self.city_postal_codes.get(user.city, "")
        if commit:
            user.save()
            self.save_m2m()
        return user
