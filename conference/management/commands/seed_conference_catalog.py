from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from conference.models import ConferencePackage, ConferenceService, ConferenceVenue


VENUES = (
    {
        "name": "Trianon Convention Centre",
        "location": "Quatre Bornes, Mauritius",
        "description": (
            "A majestic, high-ceilinged ballroom built for large-scale summits, "
            "international keynotes and gala dinners. Tiered or theatre-style "
            "seating, a full-size stage and a grand foyer for registration and "
            "networking make it the natural home for our biggest audiences, "
            "with room for up to 500 attendees."
        ),
        "image": "conference/images/conference_venue_trianon.png",
        "capacity": 500,
    },
    {
        "name": "Voila Hotel",
        "location": "Bagatelle, Mauritius",
        "description": (
            "A polished, acoustically insulated hotel setting made for "
            "executive strategy days, confidential board meetings and focused "
            "panel discussions. Quiet breakout rooms, reliable connectivity and "
            "attentive hotel service keep every session on schedule for up to "
            "150 attendees."
        ),
        "image": "conference/images/conference_venue_voila.png",
        "capacity": 150,
    },
    {
        "name": "Caudan Arts Centre",
        "location": "Port Louis, Mauritius",
        "description": (
            "An agile, design-led space on the Port Louis waterfront with "
            "modular partitions and interactive display areas. Ideal for "
            "workshops, product launches and creative brainstorming, it "
            "reconfigures easily from one open hall to several breakout rooms "
            "for up to 200 attendees."
        ),
        "image": "conference/images/conference_venue_caudan.png",
        "capacity": 200,
    },
)

PACKAGES = (
    {
        "name": "Starter Plan",
        "tagline": "Focused assemblies",
        "features": (
            "Dedicated room for exactly 50 attendees\n"
            "Theatre or classroom seating arranged to your agenda\n"
            "High-definition projector or screen, podium and microphone kit\n"
            "Technician on hand to set up and support the AV during your session\n"
            "4-hour exclusive session\n"
            "Event coordinator to run your timeline on the day\n"
            "Catering and recording not included (add them as optional services)"
        ),
        "price": Decimal("80000"),
        "min_guests": 50,
        "max_guests": 50,
    },
    {
        "name": "Professional Plan",
        "tagline": "High-end live events",
        "features": (
            "Space for 50 to 200 attendees\n"
            "Stage, lectern, confidence monitor and wireless microphones\n"
            "Multi-camera streaming set-up for remote attendees\n"
            "Registration desk and welcome team for arrivals\n"
            "Up to 6-hour session with a working lunch break\n"
            "Event coordinator from setup to close\n"
            "Recording and branding not included (add them as optional services)"
        ),
        "price": Decimal("140000"),
        "min_guests": 50,
        "max_guests": 200,
    },
    {
        "name": "Enterprise Plan",
        "tagline": "Landmark summits",
        "features": (
            "Exclusive use of the venue for 50 to 500 attendees, with no other events\n"
            "Custom stage, lighting and large-format screens planned with you\n"
            "Full production crew: audio, video and lighting technicians\n"
            "Formal welcome reception and networking break\n"
            "Dedicated hospitality team and VIP guest handling\n"
            "Event coordinator who plans with you beforehand and runs the day\n"
            "Up to 6 hours on the day of your event"
        ),
        "price": Decimal("200000"),
        "min_guests": 50,
        "max_guests": 500,
    },
)

SERVICES = (
    {
        "name": "Stage Design & Branding",
        "description": (
            "Backdrops, stage sets, screen content and signage that carry your "
            "brand from the registration desk to the keynote stage, designed "
            "and installed by our team so the room looks as considered as the "
            "agenda."
        ),
        "highlights": "Custom Backdrops\nPremium Signage\nScreen Content",
        "image": "conference/images/conference_services_branding.png",
    },
    {
        "name": "Live Streaming & Recording",
        "description": (
            "Take every session beyond the room with crystal-clear 4K video, "
            "live streaming for remote attendees and clean audio capture, "
            "followed by edited recordings you can share and keep."
        ),
        "highlights": "4K Broadcast\nRemote Attendees\nPost Production",
        "image": "conference/images/conference_services_recordings.png",
    },
    {
        "name": "Corporate Catering",
        "description": (
            "Fresh, generous menus served with an easy rhythm, from morning "
            "pastries and coffee to working lunches and afternoon refreshments, "
            "so your attendees stay energised from the first session to the "
            "last."
        ),
        "highlights": "Working Lunch\nCoffee Breaks\nNetworking Bar",
        "image": "conference/images/conference_services_catering.png",
    },
)


class Command(BaseCommand):
    help = (
        "Create or refresh the default Conference venues, packages and "
        "services. Admin-managed prices, guest limits and active state are "
        "never overwritten."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        for model, items in (
            (ConferenceVenue, VENUES),
            (ConferencePackage, PACKAGES),
            (ConferenceService, SERVICES),
        ):
            for position, item in enumerate(items, start=1):
                values = dict(item)
                name = values.pop("name")
                # Prices and guest limits are only set when first created.
                initial = {
                    key: values.pop(key)
                    for key in ("price", "capacity", "min_guests", "max_guests")
                    if key in values
                }
                obj, was_created = model.objects.get_or_create(
                    name=name,
                    defaults={**values, **initial, "position": position},
                )
                if was_created:
                    created += 1
                else:
                    for field, value in values.items():
                        setattr(obj, field, value)
                    obj.save(update_fields=list(values))
        self.stdout.write(self.style.SUCCESS(f"Conference catalogue ready ({created} new)."))
