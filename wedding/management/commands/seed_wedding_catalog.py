from django.core.management.base import BaseCommand
from django.db import transaction

from wedding.models import WeddingPackage, WeddingService, WeddingVenue


VENUES = (
    {
        "name": "Island View Hall",
        "location": "Petit Raffray, Mauritius",
        "description": "A refined setting for an intimate celebration.",
        "image": "wedding/images/wedding_venue_island_hall.png",
    },
    {
        "name": "Seven Golden Rays",
        "location": "Nouvelle France, Mauritius",
        "description": "A historic estate with elegant ballrooms and grounds.",
        "image": "wedding/images/wedding_venue_seven_rays.png",
    },
    {
        "name": "Domaine Des Aubineaux",
        "location": "Curepipe, Mauritius",
        "description": "A colonial tea estate surrounded by gardens.",
        "image": "wedding/images/wedding_venue_domain_abineaux.png",
    },
)

PACKAGES = (
    {
        "name": "Elopement Soirée",
        "slug": "elopement-soiree",
        "tagline": "The Intimate Gathering",
        "description": "Intimate wedding planning, floral design, a champagne toast, and photography.",
        "features": (
            "Bespoke elopement planner\n"
            "Luxury floral design & backdrop\n"
            "Pre-ceremony champagne toast\n"
            "Dedicated photographer (4 Hours)"
        ),
        "min_guests": 1,
        "max_guests": None,
    },
    {
        "name": "Classic Heritage",
        "slug": "classic-heritage",
        "tagline": "Signature Grandeur",
        "description": "Full-service wedding planning, venue sourcing, dining design, and photography.",
        "features": (
            "Full-service weekend curation\n"
            "Elite venue sourcing & buyout\n"
            "Cocktail & premium dining design\n"
            "Cinematography & photography team"
        ),
        "min_guests": 1,
        "max_guests": None,
    },
    {
        "name": "Royal Imperial",
        "slug": "royal-imperial",
        "tagline": "The Masterpiece Studio",
        "description": "Multi-day celebration planning with guest concierge and full production support.",
        "features": (
            "Multi-day celebration planning\n"
            "Celebrity guest concierge\n"
            "3D custom floorplan & renders\n"
            "Symphony orchestra procurement"
        ),
        "min_guests": 1,
        "max_guests": None,
    },
)

SERVICES = (
    {
        "name": "Symphonic Entertainment",
        "description": "Live music, DJs, and curated sound.",
        "highlights": "Premium Soundscapes\nElite Curators\nLive Orchestral Integration",
        "image": "wedding/images/wedding_services_entertainment.png",
    },
    {
        "name": "Immersive Scenography",
        "description": "Floral installations, drapery, and event lighting.",
        "highlights": "Custom Floral Art\nLighting Mastery\nTable Curation",
        "image": "wedding/images/wedding_services_scenes.png",
    },
    {
        "name": "Gourmet Gastronomy",
        "description": "Custom dining, wine pairings, and wedding cakes.",
        "highlights": "Bespoke Banquets\nSommelier Selection\nCrafted Patisserie",
        "image": "wedding/images/wedding_services_gastronomy.png",
    },
)


class Command(BaseCommand):
    help = (
        "Create missing wedding catalogue items. Existing items keep their "
        "names, prices, descriptions and availability; only blank fields are filled."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        created_count = 0
        for model, entries in (
            (WeddingVenue, VENUES),
            (WeddingPackage, PACKAGES),
            (WeddingService, SERVICES),
        ):
            for position, entry in enumerate(entries):
                item, created = model.objects.get_or_create(
                    name=entry["name"],
                    defaults={**entry, "position": position},
                )
                if created:
                    created_count += 1
                    continue
                changed = []
                for field, value in entry.items():
                    if value and not getattr(item, field):
                        setattr(item, field, value)
                        changed.append(field)
                if changed:
                    item.save(update_fields=changed)

        self.stdout.write(
            self.style.SUCCESS(
                f"Wedding catalogue seeded ({created_count} created). Set prices in "
                "superadmin before offering packages for booking."
            )
        )
