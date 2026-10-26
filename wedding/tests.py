import io
from decimal import Decimal

from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import WeddingPackage, WeddingService, WeddingVenue
from .pricing import calculate_estimate


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
        self.assertContains(response, "Plan your event")
        self.assertContains(response, "wedding/js/wedding.js")
        self.assertNotContains(response, "Contact our team")
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

    def test_page_renders_catalogue_with_price_on_request_items(self):
        WeddingVenue.objects.create(name="Test Hall", location="Test Town")
        WeddingPackage.objects.create(
            name="Test Package", slug="test-package", price=Decimal("1000.00")
        )
        WeddingService.objects.create(name="Test Service")

        response = self.client.get(reverse("wedding:wedding"))

        self.assertContains(response, "Test Hall")
        self.assertContains(response, "Test Package")
        self.assertContains(response, "Test Service")
        self.assertContains(response, "Price on request")


class WeddingPricingTests(TestCase):
    def test_unpriced_items_add_nothing_to_estimate(self):
        venue = WeddingVenue.objects.create(name="Hall", location="Town")
        package = WeddingPackage.objects.create(
            name="Pkg", slug="pkg", price=Decimal("1000.00")
        )
        service = WeddingService.objects.create(name="Music")

        total, lines = calculate_estimate(venue, package, [service], guests=10)

        self.assertEqual(total, Decimal("1000.00"))
        self.assertEqual(lines[0]["note"], "Price on request")
        self.assertIsNone(lines[2]["subtotal"])


class WeddingSeedCommandTests(TestCase):
    def test_reseeding_keeps_existing_prices_and_copy(self):
        call_command("seed_wedding_catalog", stdout=io.StringIO())
        package = WeddingPackage.objects.get(slug="elopement-soiree")
        package.price = Decimal("99999.00")
        package.description = "Edited by superadmin"
        package.save()

        call_command("seed_wedding_catalog", stdout=io.StringIO())

        package.refresh_from_db()
        self.assertEqual(package.price, Decimal("99999.00"))
        self.assertEqual(package.description, "Edited by superadmin")
        self.assertEqual(WeddingPackage.objects.filter(slug="elopement-soiree").count(), 1)
