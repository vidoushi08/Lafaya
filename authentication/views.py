from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetConfirmView
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect, render
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import (
    CustomerRegistrationForm,
    EmailLoginForm,
    PasswordResetTrackingSetPasswordForm,
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
        form.save()
        messages.success(request, "Your customer account has been created. You can now sign in.")
        return redirect("authentication:login")

    return render(request, "authentication/register.html", {"form": form})


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
