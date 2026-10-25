from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, call_command


CATALOG_MODELS = {
    "birthday": (
        "BirthdayVenue",
        "BirthdayPackage",
        "BirthdayService",
    ),
    "car_events": (
        "Venue",
        "EventPackage",
        "PackageFeature",
        "ExtraService",
    ),
    "conference": (
        "ConferenceVenue",
        "ConferencePackage",
        "ConferenceService",
    ),
    "seaside": (
        "SeasideVenue",
        "SeasidePackage",
        "SeasideService",
    ),
    "wedding": (
        "WeddingPackage",
        "WeddingVenue",
        "WeddingService",
    ),
}


class Command(BaseCommand):
    help = "Export approved catalogue models to app fixture files."

    def add_arguments(self, parser):
        parser.add_argument(
            "apps",
            nargs="*",
            choices=tuple(CATALOG_MODELS),
            help="Catalogue apps to export (default: all).",
        )
        parser.add_argument(
            "--output-dir",
            type=Path,
            default=settings.BASE_DIR,
            help="Directory containing the app folders (default: project root).",
        )

    def handle(self, *args, **options):
        apps = options["apps"] or CATALOG_MODELS.keys()
        output_dir = options["output_dir"]

        for app_label in apps:
            fixture_dir = output_dir / app_label / "fixtures"
            fixture_dir.mkdir(parents=True, exist_ok=True)
            fixture_path = fixture_dir / f"{app_label}_catalog.json"
            model_labels = [
                f"{app_label}.{model_name}"
                for model_name in CATALOG_MODELS[app_label]
            ]
            fixture_content = StringIO()

            call_command(
                "dumpdata",
                *model_labels,
                indent=2,
                stdout=fixture_content,
            )
            fixture_path.write_text(fixture_content.getvalue(), encoding="utf-8")
            self.stdout.write(f"Exported {app_label} catalogue to {fixture_path}")
