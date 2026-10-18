from django.shortcuts import render

from .models import SeasidePackage, SeasideService, SeasideVenue


def index(request):
    venues = SeasideVenue.objects.filter(is_active=True)
    packages = SeasidePackage.objects.filter(is_active=True)
    services = SeasideService.objects.filter(is_active=True)

    return render(
        request,
        "seaside/seaside.html",
        {
            "venues": venues,
            "packages": packages,
            "services": services,
        },
    )
