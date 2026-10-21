from django.core.management import BaseCommand

from booking.signals import backfill_existing_requests


class Command(BaseCommand):
    help = (
        "Create the missing Booking rows for theme booking requests and "
        "refresh their snapshots."
    )

    def handle(self, *args, **options):
        created = backfill_existing_requests()
        self.stdout.write(
            self.style.SUCCESS(f"Created {created} missing booking row(s).")
        )
