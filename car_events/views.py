from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import CarEventEnquiryForm
from .models import EventPackage, ExtraService, Venue


def index(request):
    venues = Venue.objects.filter(is_active=True)
    packages = EventPackage.objects.filter(is_active=True).prefetch_related("features")
    extras = ExtraService.objects.filter(is_active=True)

    if request.method == "POST":
        form = CarEventEnquiryForm(request.POST)
        if form.is_valid():
            enquiry = form.save(commit=False)
            if request.user.is_authenticated:
                enquiry.customer = request.user
            enquiry.save()
            form.save_m2m()
            messages.success(
                request,
                "Your car event enquiry was submitted successfully. "
                "Our team will contact you soon.",
            )
            return redirect("car_events:car_events")
    else:
        initial = {}
        if request.user.is_authenticated:
            initial["full_name"] = request.user.get_full_name()
            initial["email"] = request.user.email
        form = CarEventEnquiryForm(initial=initial)

    return render(
        request,
        "car_events/car_events.html",
        {
            "venues": venues,
            "packages": packages,
            "extras": extras,
            "form": form,
        },
    )
