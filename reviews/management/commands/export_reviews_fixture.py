from pathlib import Path

from django.conf import settings
from django.core import serializers
from django.core.management import BaseCommand

from reviews.models import Review, ReviewShowcase


class Command(BaseCommand):
    help = "Export anonymized published review snapshots to the reviews fixture."

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
        snapshots_by_key = {
            snapshot.source_key: snapshot
            for snapshot in ReviewShowcase.objects.filter(
                source_key__startswith="published-review-"
            )
        }
        reviews = Review.objects.filter(
            status=Review.Status.PUBLISHED
        ).select_related("booking").order_by("created_at", "pk")
        for review in reviews:
            snapshots_by_key[f"published-review-{review.pk}"] = ReviewShowcase(
                source_key=f"published-review-{review.pk}",
                display_name="Lafaya customer",
                event_type=review.booking.event_type,
                event_date=review.booking.event_date,
                rating=review.rating,
                comment=review.comment,
                created_at=review.created_at,
            )
        snapshots = sorted(
            snapshots_by_key.values(),
            key=lambda snapshot: (snapshot.created_at, snapshot.source_key),
        )
        fixture_content = serializers.serialize("json", snapshots, indent=2)
        fixture_path.write_text(fixture_content + "\n", encoding="utf-8")
        self.stdout.write(
            f"Exported {len(snapshots)} anonymized published reviews to {fixture_path}"
        )
