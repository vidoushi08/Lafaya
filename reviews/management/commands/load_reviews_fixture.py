import json
from pathlib import Path

from django.conf import settings
from django.core import serializers
from django.core.management import BaseCommand, CommandError
from django.db import transaction

from reviews.models import ReviewShowcase


class Command(BaseCommand):
    help = "Load anonymized review snapshots without importing customer or booking records."

    def add_arguments(self, parser):
        parser.add_argument(
            "fixture",
            nargs="?",
            type=Path,
            default=settings.BASE_DIR / "reviews" / "fixtures" / "reviews_catalogue.json",
            help="Review fixture path (default: reviews/fixtures/reviews_catalogue.json).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        fixture_path = options["fixture"]
        if not fixture_path.is_file():
            raise CommandError(f"Review fixture does not exist: {fixture_path}")

        try:
            objects = list(
                serializers.deserialize("json", fixture_path.read_text(encoding="utf-8"))
            )
        except (json.JSONDecodeError, serializers.DeserializationError) as error:
            raise CommandError(f"Could not read review fixture {fixture_path}: {error}") from error

        source_keys = []
        for deserialized in objects:
            if deserialized.object.__class__ is not ReviewShowcase:
                raise CommandError(
                    "Review fixtures may contain only anonymized review snapshots; "
                    f"found {deserialized.object._meta.label}."
                )

            snapshot = deserialized.object
            if not snapshot.source_key.startswith("published-review-"):
                raise CommandError(
                    f"Invalid review fixture key: {snapshot.source_key!r}"
                )

            defaults = {
                field.name: getattr(snapshot, field.attname)
                for field in snapshot._meta.concrete_fields
                if not field.primary_key
            }
            ReviewShowcase.objects.update_or_create(
                source_key=snapshot.source_key,
                defaults=defaults,
            )
            source_keys.append(snapshot.source_key)

        stale = ReviewShowcase.objects.filter(
            source_key__startswith="published-review-"
        )
        if source_keys:
            stale = stale.exclude(source_key__in=source_keys)
        deleted_count, _ = stale.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded {len(source_keys)} anonymized reviews "
                f"(removed {deleted_count} stale snapshots)."
            )
        )
