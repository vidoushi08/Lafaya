import io

from django.core.management import call_command
from django.test import TestCase

from .models import WeddingPackage, WeddingService, WeddingVenue


class WeddingCatalogCommandTests(TestCase):
    def test_seed_command_loads_catalog_fixture(self):
        call_command("seed_wedding_catalog", stdout=io.StringIO())

        self.assertTrue(
            WeddingPackage.objects.filter(slug="elopement-soiree").exists()
        )
        self.assertTrue(
            WeddingVenue.objects.filter(name="Island View Hall").exists()
        )
        self.assertTrue(
            WeddingService.objects.filter(name="Symphonic Entertainment").exists()
        )
