from django import forms

from .models import BirthdayEnquiry, BirthdayPackage


class BirthdayEnquiryForm(forms.ModelForm):
    package = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = BirthdayEnquiry
        fields = [
            "customer_name",
            "email",
            "phone",
            "event_date",
            "venue",
            "custom_requirements",
            "notes",
        ]
        widgets = {
            "customer_name": forms.TextInput(attrs={"required": True}),
            "email": forms.EmailInput(attrs={"required": True}),
            "phone": forms.TextInput(attrs={"required": True}),
            "event_date": forms.DateInput(attrs={"type": "date", "required": True}),
            "custom_requirements": forms.Textarea(attrs={"rows": 5}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        self.package = kwargs.pop("package", None)
        super().__init__(*args, **kwargs)

        if self.package is not None:
            if self.package.package_type == "fixed":
                self.fields["custom_requirements"].required = False
                self.fields["custom_requirements"].widget.attrs["disabled"] = True
            else:
                self.fields["custom_requirements"].required = True
                self.fields["custom_requirements"].widget.attrs.pop("disabled", None)

        if self.package is not None and self.package.default_venue_id:
            self.fields["venue"].required = False
            self.fields["venue"].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        if self.package is None:
            return cleaned_data

        package = BirthdayPackage.objects.filter(slug=self.package.slug, is_active=True).first()
        if package is None:
            raise forms.ValidationError("This package is no longer available.")

        if package.package_type == "fixed":
            cleaned_data["quoted_price"] = package.price
        else:
            cleaned_data["quoted_price"] = None

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.selected_package = self.package
        instance.quoted_price = None if self.package.package_type == "custom" else self.package.price
        if commit:
            instance.save()
        return instance
