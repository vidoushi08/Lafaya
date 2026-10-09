from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import CustomerRegistrationForm


def login_view(request):
    return render(request, "authentication/login.html")


def register_view(request):
    form = CustomerRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your customer account has been created. You can now sign in.")
        return redirect("authentication:login")

    return render(request, "authentication/register.html", {"form": form})
