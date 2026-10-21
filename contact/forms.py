from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
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

    class Meta:
        model = ContactMessage
        fields = ("name", "email", "phone", "topic", "subject", "message")
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name", "maxlength": 120}),
            "email": forms.EmailInput(attrs={"autocomplete": "email", "maxlength": 254}),
            "phone": forms.TelInput(attrs={"autocomplete": "tel", "maxlength": 32}),
            "subject": forms.TextInput(attrs={"maxlength": 160}),
            "message": forms.Textarea(attrs={"rows": 6, "maxlength": 4000}),
        }

    def clean_name(self):
        return " ".join(self.cleaned_data["name"].split())

    def clean_subject(self):
        return " ".join(self.cleaned_data["subject"].split())

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

    def save(self, commit=True):
        message = super().save(commit=False)
        if commit:
            message.save()
        return message
