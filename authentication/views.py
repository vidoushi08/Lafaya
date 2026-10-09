from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.views import PasswordResetConfirmView
from django.conf import settings
from django.db import transaction
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import (
    CustomerRegistrationForm,
    EmailAddressForm,
    EmailLoginForm,
    PasswordResetTrackingSetPasswordForm,
)
from .models import User
from .onboarding import (
    can_resend_onboarding_email,
    onboarding_token_is_valid,
    send_customer_verification,
)


def login_view(request):
    if request.user.is_authenticated:
        return redirect(_role_destination(request.user))

    form = EmailLoginForm(
        request,
        request.POST if request.method == "POST" else None,
    )
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        if user.is_superuser:
            destination = reverse("admin:index")
        elif user.account_type == user.AccountType.STAFF:
            destination = reverse("staff:staff")
        elif user.account_type == user.AccountType.CUSTOMER:
            destination = reverse("customer_dashboard:customer_dashboard")
        else:
            form.add_error(None, "This account does not have a supported account type.")
            destination = None

        if destination:
            login(request, user)
            request.session.set_expiry(
                0 if request.POST.get("remember") != "on" else None
            )
            next_url = request.POST.get("next") or request.GET.get("next")
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect(destination)

    return render(
        request,
        "authentication/login.html",
        {
            "form": form,
            "next": request.POST.get("next") or request.GET.get("next", ""),
        },
    )


def _role_destination(user):
    if user.is_superuser:
        return "admin:index"
    if user.account_type == user.AccountType.STAFF:
        return "staff:staff"
    return "customer_dashboard:customer_dashboard"


def register_view(request):
    form = CustomerRegistrationForm(
        request.POST if request.method == "POST" else None,
    )
    if request.method == "POST" and form.is_valid():
        user = form.save()
        send_customer_verification(user, request)
        return redirect("authentication:verification_sent")

    return render(request, "authentication/register.html", {"form": form})


def verification_sent_view(request):
    return render(request, "authentication/verification_sent.html")


def resend_verification_view(request):
    form = EmailAddressForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        user = User.objects.filter(
            email__iexact=form.cleaned_data["email"],
            account_type=User.AccountType.CUSTOMER,
            is_active=False,
        ).first()
        if user and can_resend_onboarding_email(user):
            send_customer_verification(user, request)
        return redirect("authentication:verification_resend_done")
    return render(request, "authentication/resend_verification.html", {"form": form})


def verification_resend_done_view(request):
    return render(request, "authentication/verification_resend_done.html")


def verify_email_view(request, uidb64, token):
    user = _get_user_from_uid(uidb64)
    verified = False
    if user is not None:
        with transaction.atomic():
            user = User.objects.select_for_update().filter(pk=user.pk).first()
            if user and onboarding_token_is_valid(
                user,
                token,
                User.AccountType.CUSTOMER,
                settings.CUSTOMER_EMAIL_VERIFICATION_TIMEOUT,
            ):
                user.is_active = True
                user.onboarding_token_hash = ""
                user.onboarding_token_created_at = None
                user.save(
                    update_fields=(
                        "is_active",
                        "onboarding_token_hash",
                        "onboarding_token_created_at",
                    )
                )
                verified = True
    return render(
        request,
        "authentication/verification_result.html",
        {"verified": verified},
    )


def staff_invitation_view(request, uidb64, token):
    user = _get_user_from_uid(uidb64)
    if not _valid_staff_invitation(user, token):
        return render(request, "authentication/staff_invitation_invalid.html")

    form = SetPasswordForm(
        user,
        request.POST if request.method == "POST" else None,
    )
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            locked_user = User.objects.select_for_update().filter(pk=user.pk).first()
            if not _valid_staff_invitation(locked_user, token):
                return render(request, "authentication/staff_invitation_invalid.html")
            locked_user.set_password(form.cleaned_data["new_password1"])
            locked_user.is_active = True
            locked_user.onboarding_token_hash = ""
            locked_user.onboarding_token_created_at = None
            locked_user.save(
                update_fields=(
                    "password",
                    "is_active",
                    "onboarding_token_hash",
                    "onboarding_token_created_at",
                )
            )
        return redirect("authentication:staff_invitation_complete")

    return render(
        request,
        "authentication/staff_invitation_setup.html",
        {"form": form},
    )


def staff_invitation_complete_view(request):
    return render(request, "authentication/staff_invitation_complete.html")


def _get_user_from_uid(uidb64):
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.filter(pk=user_id).first()
    except (TypeError, ValueError, OverflowError):
        return None


def _valid_staff_invitation(user, token):
    return bool(
        user
        and onboarding_token_is_valid(
            user,
            token,
            User.AccountType.STAFF,
            settings.STAFF_INVITATION_TIMEOUT,
        )
    )


def logout_view(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    logout(request)
    return redirect("authentication:login")


@login_required
def password_change_done_view(request):
    return render(request, "authentication/password_change_done.html")


class LafayaPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = PasswordResetTrackingSetPasswordForm
    template_name = "authentication/password_reset_confirm.html"
    success_url = reverse_lazy("authentication:password_reset_complete")
