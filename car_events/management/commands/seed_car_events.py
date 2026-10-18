from django.core.management.base import BaseCommand
from django.db import transaction

from car_events.models import EventPackage, ExtraService, PackageFeature, Venue


VENUES = (
    {
        "name": "SVICC",
        "location": "Paille, Mauritius",
        "description": (
            "A spacious indoor and outdoor setting for large-scale meets, "
            "showcases, and automotive expos."
        ),
        "image": "car_events/images/car_venue_svicc.png",
    },
    {
        "name": "Côte d'Or",
        "location": "St Pierre, Mauritius",
        "description": (
            "A high-capacity sports and entertainment destination for energetic "
            "meets and trackside experiences."
        ),
        "image": "car_events/images/car_venue_cote_dor.png",
    },
    {
        "name": "Tribeca Mall",
        "location": "Trianon, Mauritius",
        "description": (
            "A lively retail destination for community car meets, brand "
            "activations, and public showcases."
        ),
        "image": "car_events/images/car_venue_tribeca.png",
    },
)

PACKAGES = (
    {
        "name": "Starter Meet",
        "tagline": "Focused assemblies",
        "description": "",
        "is_featured": False,
        "features": (
            "Venue sourcing and booking",
            "Event-day coordination",
            "Registration planning",
            "Promotional support",
        ),
    },
    {
        "name": "Premium Meet",
        "tagline": "High-energy live events",
        "description": "",
        "is_featured": True,
        "features": (
            "Everything in Starter Meet",
            "Sponsor coordination",
            "Professional photo and video",
            "Show-and-shine programming",
        ),
    },
    {
        "name": "Festival Experience",
        "tagline": "Built around your vision",
        "description": "",
        "is_featured": False,
        "features": (
            "Multi-zone event planning",
            "Brand and sponsor activations",
            "Live entertainment coordination",
            "Full event production support",
        ),
    },
)

EXTRAS = (
    {
        "name": "VIP Experience",
        "description": (
            "Set aside premium parking, lounge access, catering, and branded "
            "passes for your special guests."
        ),
        "image": "car_events/images/car_services_vip.png",
    },
    {
        "name": "Show & Shine",
        "description": (
            "Give standout builds their moment with registrations, judging, "
            "trophies, and an awards ceremony."
        ),
        "image": "car_events/images/car_services_show.png",
    },
    {
        "name": "JDM Experience",
        "description": (
            "Bring Japanese street-car culture to life with themed branding, "
            "categories, and dedicated awards."
        ),
        "image": "car_events/images/car_services_jdm.png",
    },
)


class Command(BaseCommand):
    help = "Create or update the default car event venues, packages, features, and services."

    @transaction.atomic
    def handle(self, *args, **options):
        for venue_data in VENUES:
            Venue.objects.update_or_create(
                name=venue_data["name"], defaults=venue_data
            )

        for package_data in PACKAGES:
            package, _ = EventPackage.objects.update_or_create(
                name=package_data["name"],
                defaults={
                    key: value
                    for key, value in package_data.items()
                    if key != "features"
                },
            )
            for position, text in enumerate(package_data["features"]):
                PackageFeature.objects.update_or_create(
                    event_package=package,
                    text=text,
                    defaults={"position": position},
                )

        for extra_data in EXTRAS:
            ExtraService.objects.update_or_create(
                name=extra_data["name"], defaults=extra_data
            )

        self.stdout.write(self.style.SUCCESS("Car event content seeded successfully."))
