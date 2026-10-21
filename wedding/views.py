from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import MAX_DAYS_AHEAD, WeddingBookingForm, WeddingEnquiryForm
from .models import WeddingPackage, WeddingService, WeddingVenue
from .notifications import notify_admins_of_booking


def is_customer(user):
    return (
        user.is_authenticated
        and not user.is_superuser
        and user.account_type == user.AccountType.CUSTOMER
    )


def index(request):
    customer = request.user if is_customer(request.user) else None
    form = None
    packages = WeddingPackage.objects.filter(is_active=True)
    selected_package = None
    package_value = request.GET.get("package") or request.POST.get("package")
    if package_value:
        if str(package_value).isdigit():
            selected_package = packages.filter(pk=int(package_value)).first()
        else:
            selected_package = packages.filter(slug=package_value).first()

    if request.method == "POST":
        if customer is None:
            return HttpResponseForbidden(
                "Only signed-in customers can make a wedding booking request."
            )
        form = WeddingBookingForm(request.POST, customer=customer)
        if form.is_valid():
            booking = form.save()
            notify_admins_of_booking(booking, request)
            messages.success(
                request,
                "Your wedding booking request has been submitted and is awaiting approval.",
            )
            return redirect(f"{reverse('wedding:wedding')}#wedding-enquiry")
    elif customer is not None:
        form = WeddingBookingForm(
            initial={
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "phone": customer.phone,
                "package": selected_package.pk if selected_package else None,
            },
            customer=customer,
        )

    return render(
        request,
        "wedding/wedding.html",
        {
            "packages": packages,
            "venues": WeddingVenue.objects.filter(is_active=True),
            "services": WeddingService.objects.filter(is_active=True, price__isnull=False),
            "form": form,
            "is_customer": customer is not None,
            "selected_services": (
                form.data.getlist("optional_services")
                if form is not None and form.is_bound
                else []
            ),
            "selected_package": selected_package,
            "min_event_date": timezone.localdate().isoformat(),
            "max_event_date": (
                timezone.localdate() + timedelta(days=MAX_DAYS_AHEAD)
            ).isoformat(),
            "login_next": f"{reverse('wedding:wedding')}#wedding-enquiry",
        },
    )


@login_required
def enquiry(request):
    package_slug = request.GET.get("package") or request.POST.get("package")
    package = get_object_or_404(WeddingPackage, slug=package_slug, is_active=True)

    if request.method == "POST":
        form = WeddingEnquiryForm(request.POST)

        if form.is_valid():
            wedding_enquiry = form.save(commit=False)
            wedding_enquiry.customer = request.user
            wedding_enquiry.package = package
            wedding_enquiry.save()
            messages.success(request, "Your wedding enquiry has been submitted successfully!")
            return redirect("wedding:wedding")
    else:
        form = WeddingEnquiryForm()

    return render(
        request,
        "wedding/wedding_enquiry.html",
        {"form": form, "package": package},
    )
