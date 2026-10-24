import json
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import serializers
from django.core.management import BaseCommand

from booking.models import Booking
from reviews.models import Review


class Command(BaseCommand):
    help = (
        "Export published reviews, plus the customers and bookings they reference, "
        "to reviews/fixtures/reviews_catalogue.json."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            type=Path,
            default=settings.BASE_DIR,
            help="Directory containing the reviews app (default: project root).",
        )

    def handle(self, *args, **options):
        fixture_dir = options["output_dir"] / "reviews" / "fixtures"
        fixture_dir.mkdir(parents=True, exist_ok=True)
        fixture_path = fixture_dir / "reviews_catalogue.json"
        reviews = Review.objects.filter(status=Review.Status.PUBLISHED).order_by("created_at")
        customers = get_user_model().objects.filter(
            pk__in=reviews.values_list("customer_id", flat=True)
        )
        bookings = Booking.objects.filter(pk__in=reviews.values_list("booking_id", flat=True))

        objects = []
        objects += json.loads(serializers.serialize("json", customers, use_natural_foreign_keys=True))
        objects += json.loads(serializers.serialize("json", bookings, use_natural_foreign_keys=True))
        objects += json.loads(serializers.serialize("json", reviews))

        # Customer contact details and credentials are not needed to display reviews.
        for item in objects:
            if item["model"] == "authentication.user":
                fields = item["fields"]
                fields["password"] = "!"
                fields["email"] = ""
                fields["last_login"] = None
                fields["is_staff"] = False
                fields["is_superuser"] = False

        fixture_path.write_text(json.dumps(objects, indent=2) + "\n", encoding="utf-8")
        self.stdout.write(f"Exported {reviews.count()} published reviews to {fixture_path}")
