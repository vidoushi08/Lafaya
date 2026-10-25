from django.shortcuts import render
from django.views.decorators.http import require_safe

from .models import WeddingPackage, WeddingService, WeddingVenue


@require_safe
def index(request):
    return render(
        request,
        "wedding/wedding.html",
        {
            "packages": WeddingPackage.objects.filter(is_active=True),
            "venues": WeddingVenue.objects.filter(is_active=True),
            "services": WeddingService.objects.filter(
                is_active=True, price__isnull=False
            ),
        },
    )
