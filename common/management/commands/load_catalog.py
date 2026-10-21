from django.core.management import BaseCommand, call_command

from .export_catalog_fixtures import CATALOG_MODELS


class Command(BaseCommand):
    help = "Load every catalogue fixture into the database."

    def handle(self, *args, **options):
        fixture_names = [
            f"{app_label}_catalog" for app_label in CATALOG_MODELS
        ]
        call_command(
            "loaddata",
            *fixture_names,
            verbosity=options["verbosity"],
        )
        self.stdout.write(
            self.style.SUCCESS("Loaded " + ", ".join(fixture_names))
        )
