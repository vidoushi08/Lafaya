from django import forms

from .models import ContactMessage


class ContactForm(forms.Form):
    first_name = forms.CharField(
        max_length=60,
        label="First name",
        widget=forms.TextInput(attrs={"autocomplete": "given-name"}),
    )
    last_name = forms.CharField(
        max_length=60,
        label="Last name",
        widget=forms.TextInput(attrs={"autocomplete": "family-name"}),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autocomplete": "email", "maxlength": 254}),
    )
    message = forms.CharField(
        max_length=4000,
        label="Message",
        widget=forms.Textarea(attrs={"rows": 5, "maxlength": 4000}),
    )
    website = forms.CharField(
        required=False,
        label="",
        widget=forms.TextInput(
            attrs={
                "class": "contact-honeypot",
                "tabindex": "-1",
                "autocomplete": "off",
                "aria-hidden": "true",
            }
        ),
    )

    def clean_first_name(self):
        return " ".join(self.cleaned_data["first_name"].split())

    def clean_last_name(self):
        return " ".join(self.cleaned_data["last_name"].split())

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 10:
            raise forms.ValidationError("Please add a little more detail (at least 10 characters).")
        return message

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("website"):
            raise forms.ValidationError("Unable to submit this message.")
        return cleaned_data

    def save(self):
        name = f"{self.cleaned_data['first_name']} {self.cleaned_data['last_name']}"
        return ContactMessage.objects.create(
            name=name,
            email=self.cleaned_data["email"],
            topic=ContactMessage.Topic.GENERAL,
            subject="Website contact form",
            message=self.cleaned_data["message"],
        )
