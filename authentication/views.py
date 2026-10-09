from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import CustomerRegistrationForm, EmailLoginForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect(_role_destination(request.user))

    form = EmailLoginForm(request, request.POST or None)
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
    form = CustomerRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your customer account has been created. You can now sign in.")
        return redirect("authentication:login")

    return render(request, "authentication/register.html", {"form": form})
