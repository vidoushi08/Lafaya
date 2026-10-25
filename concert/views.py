from django.shortcuts import render
from .models import Concert, Venue, ProductionElement, TicketPackage


def concert_home(request):

    concert = Concert.objects.filter(is_active=True).first()

    venues = Venue.objects.filter(is_active=True)

    production_elements = ProductionElement.objects.all()

    ticket_packages = TicketPackage.objects.filter(is_active=True)

    context = {
        'concert': concert,
        'venues': venues,
        'production_elements': production_elements,
        'ticket_packages': ticket_packages,
    }

    return render(request, 'concert/concert.html', context)