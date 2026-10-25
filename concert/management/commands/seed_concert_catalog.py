from django.core.management.base import BaseCommand
from django.db import transaction
from concert.models import ConcertVenue, ConcertPackage, ConcertService

VENUES = ({'name': 'The Neon Dome Arena',
  'location': 'Tokyo, Japan',
  'description': 'A multi-sensory cyber dome loaded with spatial-audio arrays and '
                 '360-degree LED walls.',
  'image': 'concert/images/concert_venue_neon_arena.png'},
 {'name': 'Viper Canyon Amphitheater',
  'location': 'Colorado, USA',
  'description': 'Monolithic red rocks meet premium acoustic projection, creating '
                 'natural sonic perfection under open stars.',
  'image': 'concert/images/concert_venue_viper_theatre.png'},
 {'name': 'The Foundry Cathedral',
  'location': 'Berlin, Germany',
  'description': 'A dark industrial powerhouse delivering pure brutal aesthetics and '
                 'earth-shaking low-end bass.',
  'image': 'concert/images/concert_venue_foundry_cathedral.png'})

PACKAGES = ({'name': 'Arena Pit Pass',
  'tagline': 'Standard admission',
  'features': 'Access to general arena standing pit\n'
              'Standard digital entry pass\n'
              'High-fidelity acoustic coverage zones\n'
              'Merchandise kiosk access',
  'price': '2500',
  'price_basis': 'per_guest',
  'is_featured': False,
  'min_guests': 1,
  'max_guests': None},
 {'name': 'VIP Backstage Pass',
  'tagline': 'Elevated premium',
  'features': 'Fast-track VIP venue entrance\n'
              'Access to backstage bar & lounge\n'
              'Exclusive limited edition show poster\n'
              'Premium elevated sound stage viewing',
  'price': '5000',
  'price_basis': 'per_guest',
  'is_featured': False,
  'min_guests': 1,
  'max_guests': None},
 {'name': 'All-Access AAA',
  'tagline': 'Ultimate experience',
  'features': 'Full artist soundcheck experience\n'
              'On-stage side platform viewing area\n'
              'Bespoke catering & premium open bar\n'
              'Exclusive artist meet & greet photo',
  'price': '10000',
  'price_basis': 'per_guest',
  'is_featured': False,
  'min_guests': 1,
  'max_guests': None})

SERVICES = ({'name': 'Sonic Engineering',
  'description': 'High-fidelity spatial audio arrays providing clinical, thunderous '
                 'soundscapes. Every corner of the arena is tuned for absolute '
                 'acoustic purity.',
  'highlights': '120dB Clarity\nSpatial Arrays\nBass Curation',
  'image': 'concert/images/concert_services_sonic_engineering.png'},
 {'name': 'Laser Scenography',
  'description': 'Aesthetic visual transformations utilizing towering strobe systems, '
                 'immersive neon vectors, and custom real-time reactive stage '
                 'lighting.',
  'highlights': '3D Vector Lasers\nLive Visual Mapping\nReactive Strobes',
  'image': 'concert/images/concert_services_laser_scenes.png'},
 {'name': 'Backstage Catering',
  'description': 'Michelin-caliber culinary services, curated cocktail mixers, and '
                 'dedicated green room support for all VIP and artist spaces.',
  'highlights': 'VIP Lounge Access\nArtisanal Cocktails\nGreen Room Dining',
  'image': 'concert/images/concert_services_catering.png'})

class Command(BaseCommand):
    help = (
        "Create or refresh the default concert catalogue without overwriting "
        "prices or superadmin availability settings."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        for model, entries in (
            (ConcertVenue, VENUES),
            (ConcertPackage, PACKAGES),
            (ConcertService, SERVICES),
        ):
            for position, entry in enumerate(entries):
                item, created = model.objects.get_or_create(
                    name=entry["name"],
                    defaults={**entry, "position": position},
                )
                if not created:
                    preserved_fields = {"capacity", "min_guests", "max_guests", "price", "price_basis", "is_featured"}
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
                "Concert catalogue seeded. Set prices and price bases in superadmin "
                "before offering items for booking."
            )
        )
