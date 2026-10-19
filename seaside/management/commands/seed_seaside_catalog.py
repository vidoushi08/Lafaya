from django.core.management.base import BaseCommand
from django.db import transaction

from seaside.models import SeasidePackage, SeasideService, SeasideVenue


VENUES = (
    {
        "name": "The Glass Pavilion",
        "location": "Northern coast, Mauritius",
        "description": (
            "A bright, architectural setting for ceremonies, private dinners, "
            "and celebrations framed by white sand and blue water."
        ),
        "image": "seaside/images/seaside_venue_pavilion.png",
    },
    {
        "name": "Sunset Terrace",
        "location": "West coast, Mauritius",
        "description": (
            "An easygoing waterfront terrace for sunset receptions, long-table "
            "dining, and evenings that flow into the night."
        ),
        "image": "seaside/images/seaside_venue_terrace.png",
    },
    {
        "name": "Oceanfront Villa",
        "location": "Private island setting",
        "description": (
            "A private escape for intimate celebrations, weekend gatherings, "
            "and hosted experiences with a view in every direction."
        ),
        "image": "seaside/images/seaside_venue_villa.png",
    },
)

PACKAGES = (
    {
        "name": "Barefoot Gathering",
        "tagline": "Relaxed celebrations",
        "description": "",
        "features": (
            "Seaside setup for up to 30 guests\n"
            "On-site service team\n"
            "Sunset timeline and event coordination"
        ),
        "is_featured": False,
    },
    {
        "name": "Sunset Social",
        "tagline": "Signature celebrations",
        "description": "",
        "features": (
            "Host up to 100 guests by the water\n"
            "Music and sound system\n"
            "Full service team and event coordination"
        ),
        "is_featured": True,
    },
    {
        "name": "Private Island",
        "tagline": "Unforgettable occasions",
        "description": "",
        "features": (
            "Exclusive venue hosting for up to 250 guests\n"
            "Custom entertainment and production\n"
            "Hosted hospitality and full event coordination"
        ),
        "is_featured": False,
    },
)

SERVICES = (
    {
        "name": "Coastal styling",
        "description": (
            "Natural textures, considered florals, candlelight, and tablescapes "
            "that belong to the landscape."
        ),
        "highlights": "Tablescapes\nFlorals",
        "image": "seaside/images/seaside_services_styling.png",
    },
    {
        "name": "Photography",
        "description": (
            "Thoughtful coverage of the people, atmosphere, and small "
            "unscripted moments that make the day yours."
        ),
        "highlights": "Editorial Coverage\nGolden Hour",
        "image": "seaside/images/seaside_services_photography.png",
    },
    {
        "name": "Ocean-to-table catering",
        "description": (
            "Fresh, generous menus served with an easy rhythm from welcome "
            "aperitifs to the last toast."
        ),
        "highlights": "Fresh Menus\nBeach Bar",
        "image": "seaside/images/seaside_services_catering.png",
    },
)


DEFAULT_GUEST_LIMITS = {
    "Barefoot Gathering": {"min_guests": 1, "max_guests": 30},
    "Sunset Social": {"min_guests": 1, "max_guests": 100},
    "Private Island": {"min_guests": 1, "max_guests": 250},
}


class Command(BaseCommand):
    help = (
        "Create or refresh the default Seaside catalogue without overwriting "
        "prices or superadmin availability settings."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        for model, entries in (
            (SeasideVenue, VENUES),
            (SeasidePackage, PACKAGES),
            (SeasideService, SERVICES),
        ):
            for position, entry in enumerate(entries):
                item, created = model.objects.get_or_create(
                    name=entry["name"],
                    defaults={
                        **entry,
                        **DEFAULT_GUEST_LIMITS.get(entry["name"], {}),
                        "position": position,
                    },
                )
                if not created:
                    for field, value in entry.items():
                        setattr(item, field, value)
                    item.save(update_fields=(*entry.keys(),))

        self.stdout.write(
            self.style.SUCCESS(
                "Seaside catalogue seeded. Set prices and price bases in superadmin "
                "before offering items for booking."
            )
        )
