from django.contrib import messages
from django.shortcuts import redirect, render

from common.decorators import account_type_required
from .forms import CustomerProfileForm


@account_type_required("customer")
def index(request):
    return render(request, "customer_dashboard/dashboard.html")


@account_type_required("customer")
def manage_profile(request):
    form = CustomerProfileForm(
        request.POST or None,
        instance=request.user,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("customer_dashboard:manage_profile")

    return render(
        request,
        "customer_dashboard/manage_profile.html",
        {"form": form},
    )


@account_type_required("customer")
def booking_history(request):
    return render(request, "customer_dashboard/booking_history.html")
