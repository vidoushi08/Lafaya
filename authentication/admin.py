from django import forms
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import Group

from .admin_site import superadmin_site
from .models import User


class LafayaUserChangeForm(UserChangeForm):
    account_type = forms.ChoiceField(
        choices=[("", "---------"), (User.AccountType.CUSTOMER, "Customer")],
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("is_superuser"):
            cleaned_data["account_type"] = ""
        elif not cleaned_data.get("account_type"):
            self.add_error(
                "account_type",
                "Choose the customer account type.",
            )
        return cleaned_data


@admin.register(User, site=superadmin_site)
class LafayaUserAdmin(UserAdmin):
    form = LafayaUserChangeForm
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "account_role",
        "is_active",
        "is_staff",
        "is_superuser",
    )
    list_filter = ("account_type", "is_active", "is_staff", "is_superuser")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)
    fieldsets = UserAdmin.fieldsets + (
        ("Lafaya account", {"fields": ("account_type",)}),
        (
            "Contact details",
            {
                "fields": (
                    "phone",
                    "date_of_birth",
                    "gender",
                    "address",
                    "city",
                    "postal_code",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        return False

    @admin.display(description="Account role", ordering="account_type")
    def account_role(self, user):
        if user.is_superuser:
            return "Superadmin"
        return user.get_account_type_display()


superadmin_site.register(Group, GroupAdmin)
