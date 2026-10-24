from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    help = "Export review records to reviews/fixtures/reviews_catalogue.json."

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
        fixture_content = StringIO()
        call_command("dumpdata", "reviews.Review", indent=2, stdout=fixture_content)
        fixture_path.write_text(fixture_content.getvalue(), encoding="utf-8")
        self.stdout.write(f"Exported reviews to {fixture_path}")
