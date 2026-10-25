import io

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

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


class WeddingPageTests(TestCase):
    def test_wedding_page_shows_catalogue_without_an_enquiry_form(self):
        response = self.client.get(reverse("wedding:wedding"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bespoke Experiences")
        self.assertContains(response, "Contact our team")
        self.assertNotContains(response, "wedding-enquiry")
        self.assertNotContains(response, "Submit wedding booking request")

    def test_wedding_page_does_not_accept_booking_posts(self):
        response = self.client.post(reverse("wedding:wedding"), {})

        self.assertEqual(response.status_code, 405)
