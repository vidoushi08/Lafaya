import io

from django.core.management import call_command
from django.contrib.auth import get_user_model
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
    def test_wedding_page_shows_booking_access_for_visitors(self):
        response = self.client.get(reverse("wedding:wedding"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bespoke Experiences")
        self.assertContains(response, "Contact our team")
        self.assertContains(response, 'id="wedding-enquiry"')
        self.assertContains(response, "Sign in to book your wedding")

    def test_signed_in_customer_sees_booking_form(self):
        customer = get_user_model().objects.create_user(
            username="wedding-customer",
            email="customer@example.com",
            password="test-password",
            first_name="Taylor",
            last_name="Guest",
        )
        self.client.force_login(customer)
        response = self.client.get(reverse("wedding:wedding"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Submit wedding booking request")
        self.assertContains(response, 'value="customer@example.com"')

    def test_wedding_page_does_not_accept_booking_posts(self):
        response = self.client.post(reverse("wedding:wedding"), {})

        self.assertEqual(response.status_code, 403)
