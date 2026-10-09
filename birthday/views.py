from django.http import HttpResponseBadRequest
from django.shortcuts import redirect, render

from venues.models import EventType, Venue

from .forms import BirthdayEnquiryForm
from .models import BirthdayPackage


def _get_birthday_venues():
    birthday_type = EventType.objects.filter(slug="birthday").first()
    if birthday_type is None:
        return Venue.objects.none()
    return Venue.objects.filter(event_types=birthday_type).distinct()


def _resolve_package(value):
    if value is None:
        return None

    cleaned = str(value).strip()
    if not cleaned:
        return None

    package_qs = BirthdayPackage.objects.filter(is_active=True)
    if cleaned.isdigit():
        return package_qs.filter(pk=int(cleaned)).first()
    return package_qs.filter(slug=cleaned).first()


def index(request):
    package_param = request.GET.get("package") or request.POST.get("package")
    package = _resolve_package(package_param) if package_param else None
    context = {
        "selected_package": package,
        "birthday_venues": _get_birthday_venues(),
    }
    if package is not None:
        context["form"] = BirthdayEnquiryForm(package=package)
    return render(request, "birthday/birthday.html", context)


def enquiry(request):
    package_param = request.GET.get("package") or request.POST.get("package") or request.POST.get("package_slug")
    package = _resolve_package(package_param) if package_param else None

    if package_param and package is None:
        return HttpResponseBadRequest("Invalid or inactive package selected.")

    if request.method == "POST":
        if package is None:
            return HttpResponseBadRequest("A valid package selection is required.")

        form = BirthdayEnquiryForm(request.POST, package=package)
        if form.is_valid():
            enquiry = form.save(commit=False)
            enquiry.selected_package = package
            enquiry.quoted_price = package.price if package.package_type == "fixed" else None
            enquiry.save()
            return redirect("birthday:birthday")
    else:
        form = BirthdayEnquiryForm(package=package)

    context = {
        "selected_package": package,
        "form": form,
        "birthday_venues": _get_birthday_venues(),
    }
    return render(request, "birthday/birthday.html", context)
