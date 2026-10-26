from django.core.management.base import BaseCommand
from django.db import transaction

from birthday.models import BirthdayPackage, BirthdayService, BirthdayVenue


VENUES = (
    {
        "name": "Grand Ballroom",
        "location": "Central Mauritius",
        "description": (
            "An elegant ballroom with chandeliers, generous dining space, and "
            "room for a polished milestone celebration."
        ),
        "image": "birthday/images/birthday_venue_ballroom.png",
        "capacity": 300,
    },
    {
        "name": "Sunset Terrace",
        "location": "West coast, Mauritius",
        "description": (
            "An open-air garden terrace for sunset dinners, family gatherings, "
            "and relaxed celebrations under the lights."
        ),
        "image": "birthday/images/birthday_venue_terrace.png",
        "capacity": 150,
    },
    {
        "name": "Playhouse",
        "location": "Mauritius",
        "description": (
            "A playful indoor setting with room for games, activities, and "
            "lively birthday parties for all ages."
        ),
        "image": "birthday/images/birthday_venue_factory.png",
        "capacity": 200,
    },
)

PACKAGES = (
    {
        "name": "Little Moments",
        "tagline": "Intimate celebrations",
        "description": "",
        "features": (
            "Birthday setup for up to 50 guests\n"
            "Tables, chairs and a welcoming celebration layout\n"
            "Birthday styling for the cake and gift area\n"
            "Event coordinator to manage the timeline on the day\n"
            "Food and entertainment can be added to suit your celebration"
        ),
        "is_featured": False,
        "min_guests": 1,
        "max_guests": 50,
    },
    {
        "name": "Signature Celebration",
        "tagline": "Thoughtful, joyful gatherings",
        "description": "",
        "features": (
            "Birthday setup for up to 150 guests\n"
            "Tables, chairs and lounge-style seating\n"
            "Birthday styling for the main celebration space\n"
            "Sound system and background music\n"
            "Event coordinator from setup to close\n"
            "Food and entertainment can be added to suit your celebration"
        ),
        "is_featured": True,
        "min_guests": 1,
        "max_guests": 150,
    },
    {
        "name": "Milestone Experience",
        "tagline": "A celebration to remember",
        "description": "",
        "features": (
            "Celebration setup for up to 300 guests\n"
            "Dedicated event coordinator and on-site team\n"
            "Signature styling for the venue and birthday moment\n"
            "Entertainment and production planned around your vision\n"
            "Guest experience coordinated from arrival to the final toast\n"
            "Food and entertainment can be tailored to your event"
        ),
        "is_featured": False,
        "min_guests": 1,
        "max_guests": 300,
    },
)

SERVICES = (
    {
        "name": "Birthday styling",
        "description": (
            "A celebration look shaped around the guest of honour, with "
            "considered florals, balloons, tablescapes, and a memorable cake display."
        ),
        "highlights": "Personalised decor\nCake display",
        "image": "birthday/images/birthday_services_styling.png",
    },
    {
        "name": "Gastronomy",
        "description": (
            "From sharing platters to a seated dinner, menus and drinks are "
            "planned to suit your guests and the way you want to celebrate."
        ),
        "highlights": "Custom menus\nDrinks service",
        "image": "birthday/images/birthday_services_gastronomy.png",
    },
    {
        "name": "Entertainment",
        "description": (
            "Keep the celebration moving with music, DJs, live performers, "
            "and age-appropriate activities for your guests."
        ),
        "highlights": "DJ and live music\nGames and activities",
        "image": "birthday/images/birthday_services_entertainment.png",
    },
)


class Command(BaseCommand):
    help = (
        "Create or refresh the default birthday catalogue without overwriting "
        "prices or superadmin availability settings."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        for model, entries in (
            (BirthdayVenue, VENUES),
            (BirthdayPackage, PACKAGES),
            (BirthdayService, SERVICES),
        ):
            for position, entry in enumerate(entries):
                item, created = model.objects.get_or_create(
                    name=entry["name"],
                    defaults={**entry, "position": position},
                )
                if not created:
                    preserved_fields = {"capacity", "min_guests", "max_guests"}
                    for field, value in entry.items():
                        if field in preserved_fields:
                            continue
                        setattr(item, field, value)
                    update_fields = tuple(
                        field for field in entry if field not in preserved_fields
                    )
                    item.save(update_fields=update_fields)

        self.stdout.write(
            self.style.SUCCESS(
                "Birthday catalogue seeded. Set prices and price bases in superadmin "
                "before offering items for booking."
            )
        )
