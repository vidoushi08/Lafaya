from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import WeddingPackage
from .forms import WeddingEnquiryForm


def index(request):
    packages = WeddingPackage.objects.filter(is_active=True)

    return render(
        request,
        "wedding/wedding.html",
        {"packages": packages},
    )


@login_required
def enquiry(request):
    package_slug = request.GET.get("package") or request.POST.get("package")

    package = get_object_or_404(
        WeddingPackage,
        slug=package_slug,
        is_active=True,
    )

    if request.method == "POST":
        form = WeddingEnquiryForm(request.POST)

        if form.is_valid():
            wedding_enquiry = form.save(commit=False)
            wedding_enquiry.customer = request.user
            wedding_enquiry.package = package
            wedding_enquiry.save()

            messages.success(
                request,
                "Your wedding enquiry has been submitted successfully!",
            )

            return redirect("wedding:wedding")
    else:
        form = WeddingEnquiryForm()

    return render(
        request,
        "wedding/wedding_enquiry.html",
        {
            "form": form,
            "package": package,
        },
    )