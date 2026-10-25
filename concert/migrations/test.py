from django.test import TestCase
from .models import Concert, Venue, ProductionElement, TicketPackage


class ConcertModelTest(TestCase):

    def test_concert_creation(self):
        concert = Concert.objects.create(
            title="Experience Live Music Reborn",
            subtitle="Engineered for Pure Acoustic Energy",
            description="Experience unforgettable live music.",
            is_active=True
        )

        self.assertEqual(
            concert.title,
            "Experience Live Music Reborn"
        )


class VenueModelTest(TestCase):

    def test_venue_creation(self):
        venue = Venue.objects.create(
            name="The Neon Dome Arena",
            location="Tokyo, Japan",
            description="A futuristic concert arena."
        )

        self.assertEqual(
            venue.location,
            "Tokyo, Japan"
        )


class TicketPackageTest(TestCase):

    def test_ticket_package_price(self):
        package = TicketPackage.objects.create(
            tier="Standard Admission",
            name="Aria Pit Pass",
            price=2500,
            description="General admission concert access."
        )

        self.assertEqual(package.price, 2500)