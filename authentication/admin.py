from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from .admin_site import superadmin_site
from .models import User
from .onboarding import can_resend_onboarding_email, send_staff_invitation


class LafayaUserChangeForm(UserChangeForm):
    account_type = forms.ChoiceField(
        choices=[("", "---------"), *User.AccountType.choices],
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("is_superuser"):
            cleaned_data["account_type"] = ""
        elif not cleaned_data.get("account_type"):
            self.add_error(
                "account_type",
                "Choose whether this account is a customer or staff member.",
            )
        return cleaned_data


class LafayaUserCreationForm(forms.ModelForm):
    account_type = forms.ChoiceField(
        choices=((User.AccountType.STAFF, "Staff"),),
        disabled=True,
        initial=User.AccountType.STAFF,
    )

    class Meta:
        model = User
        fields = ("username", "email", "account_type")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.account_type = User.AccountType.STAFF
        user.is_active = False
        user.set_unusable_password()
        if commit:
            user.save()
            self.save_m2m()
        return user


@admin.action(description="Resend staff setup invitation")
def resend_staff_invitation(modeladmin, request, queryset):
    sent = 0
    skipped = 0
    for user in queryset:
        is_pending_staff = (
            user.account_type == User.AccountType.STAFF
            and not user.is_active
            and not user.has_usable_password()
            and bool(user.onboarding_token_hash)
        )
        if not is_pending_staff or not can_resend_onboarding_email(user):
            skipped += 1
            continue
        send_staff_invitation(user, request)
        sent += 1

    if sent:
        modeladmin.message_user(
            request,
            f"Sent {sent} staff setup invitation(s). Previous links were invalidated.",
            messages.SUCCESS,
        )
    if skipped:
        modeladmin.message_user(
            request,
            f"Skipped {skipped} account(s): they are not pending staff invitations "
            "or are still within the resend cooldown.",
            messages.WARNING,
        )


@admin.register(User, site=superadmin_site)
class LafayaUserAdmin(UserAdmin):
    form = LafayaUserChangeForm
    add_form = LafayaUserCreationForm
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
    actions = (resend_staff_invitation,)
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "account_type",
                ),
            },
        ),
    )
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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change and obj.account_type == User.AccountType.STAFF:
            send_staff_invitation(obj, request)

    @admin.display(description="Account role", ordering="account_type")
    def account_role(self, user):
        if user.is_superuser:
            return "Superadmin"
        return user.get_account_type_display()


superadmin_site.register(Group, GroupAdmin)
