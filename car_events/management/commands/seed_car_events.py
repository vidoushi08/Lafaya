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
        "highlights": "Premium parking\nLounge access",
        "image": "car_events/images/car_services_vip.png",
    },
    {
        "name": "Show & Shine",
        "description": (
            "Give standout builds their moment with registrations, judging, "
            "trophies, and an awards ceremony."
        ),
        "highlights": "Judging\nAwards ceremony",
        "image": "car_events/images/car_services_show.png",
    },
    {
        "name": "JDM Experience",
        "description": (
            "Bring Japanese street-car culture to life with themed branding, "
            "categories, and dedicated awards."
        ),
        "highlights": "Themed categories\nDedicated awards",
        "image": "car_events/images/car_services_jdm.png",
    },
)


class Command(BaseCommand):
    help = (
        "Create or refresh the default car event catalogue without overwriting "
        "prices or superadmin availability settings."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        for model, entries in (
            (Venue, VENUES),
            (EventPackage, PACKAGES),
            (ExtraService, EXTRAS),
        ):
            for position, entry in enumerate(entries):
                defaults = {
                    key: value
                    for key, value in entry.items()
                    if key != "features"
                }
                item, created = model.objects.get_or_create(
                    name=entry["name"],
                    defaults={**defaults, "position": position},
                )
                if not created:
                    for field, value in defaults.items():
                        setattr(item, field, value)
                    item.save(update_fields=(*defaults.keys(),))

                if model is EventPackage:
                    for feature_position, text in enumerate(entry["features"]):
                        PackageFeature.objects.update_or_create(
                            event_package=item,
                            text=text,
                            defaults={"position": feature_position},
                        )

        self.stdout.write(
            self.style.SUCCESS(
                "Car event catalogue seeded. Set prices and price bases in superadmin "
                "before offering items for booking."
            )
        )
