from django.core.management.base import BaseCommand
from django.db import transaction

from wedding.models import WeddingPackage, WeddingService, WeddingVenue


PACKAGES = (
    ("elopement-soiree", "Elopement Soirée", "Intimate wedding planning, floral design, a champagne toast, and photography.", "125000.00"),
    ("classic-heritage", "Classic Heritage", "Full-service wedding planning, venue sourcing, dining design, and photography.", "180000.00"),
    ("royal-imperial", "Royal Imperial", "Multi-day celebration planning with guest concierge and full production support.", "210000.00"),
)

VENUES = (
    ("Island View Hall", "Petit Raffray, Mauritius", "A refined setting for an intimate celebration.", "wedding/images/wedding_venue_island_hall.png"),
    ("Seven Golden Rays", "Nouvelle France, Mauritius", "A historic estate with elegant ballrooms and grounds.", "wedding/images/wedding_venue_seven_rays.png"),
    ("Domaine Des Aubineaux", "Curepipe, Mauritius", "A colonial tea estate surrounded by gardens.", "wedding/images/wedding_venue_domain_abineaux.png"),
)

SERVICES = (
    ("Symphonic Entertainment", "Live music, DJs, and curated sound.", 1),
    ("Immersive Scenography", "Floral installations, drapery, and event lighting.", 2),
    ("Gourmet Gastronomy", "Custom dining, wine pairings, and wedding cakes.", 3),
)


class Command(BaseCommand):
    help = "Create the default wedding packages, venues, and optional services."

    @transaction.atomic
    def handle(self, *args, **options):
        for position, (slug, name, description, price) in enumerate(PACKAGES, 1):
            package, created = WeddingPackage.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "description": description,
                    "price": price,
                    "display_order": position,
                },
            )
            if not created:
                package.name = name
                package.description = description
                package.display_order = position
                package.save(update_fields=("name", "description", "display_order"))

        for position, (name, location, description, image) in enumerate(VENUES, 1):
            WeddingVenue.objects.update_or_create(
                name=name,
                defaults={
                    "location": location,
                    "description": description,
                    "image": image,
                    "position": position,
                },
            )

        for position, (name, description, _) in enumerate(SERVICES, 1):
            WeddingService.objects.update_or_create(
                name=name,
                defaults={"description": description, "position": position},
            )

        self.stdout.write(self.style.SUCCESS("Wedding catalogue is ready."))
