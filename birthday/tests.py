from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from venues.models import EventType, Venue

from .models import BirthdayEnquiry, BirthdayPackage


class BirthdayPackageEnquiryTests(TestCase):
    def setUp(self):
        self.birthday_type = EventType.objects.create(name="Birthday", slug="birthday")
        self.venue = Venue.objects.create(
            name="Grand Ballroom",
            location="Mauritius",
            price=Decimal("2500.00"),
        )
        self.venue.event_types.add(self.birthday_type)

        self.starter = BirthdayPackage.objects.create(
            name="Starter",
            slug="starter",
            package_type="fixed",
            price=Decimal("850.00"),
            description="Venue styling and light planning.",
            display_order=1,
            is_active=True,
        )
        self.professional = BirthdayPackage.objects.create(
            name="Professional",
            slug="professional",
            package_type="fixed",
            price=Decimal("1700.00"),
            description="Full design and production.",
            display_order=2,
            is_active=True,
        )
        self.custom = BirthdayPackage.objects.create(
            name="Custom",
            slug="custom",
            package_type="custom",
            price=None,
            description="Fully customised quote.",
            display_order=3,
            is_active=True,
        )

    def test_starter_and_professional_prices_are_correct(self):
        self.assertEqual(self.starter.price, Decimal("850.00"))
        self.assertEqual(self.professional.price, Decimal("1700.00"))
        self.assertIsNone(self.custom.price)

    def test_invalid_package_slug_is_rejected(self):
        response = self.client.get(reverse("birthday:enquiry"), {"package": "fake-slug"})
        self.assertEqual(response.status_code, 400)

    def test_browser_manipulated_price_is_ignored(self):
        response = self.client.post(
            reverse("birthday:enquiry"),
            {
                "customer_name": "Alicia Brown",
                "email": "alicia@example.com",
                "phone": "+230 5123 4567",
                "event_date": "2027-02-12",
                "venue": str(self.venue.id),
                "package": str(self.starter.id),
                "quoted_price": "999.99",
                "notes": "Prefer a warm indoor setup.",
            },
        )
        self.assertEqual(response.status_code, 302)
        saved = BirthdayEnquiry.objects.get(customer_name="Alicia Brown")
        self.assertEqual(saved.selected_package_id, self.starter.id)
        self.assertEqual(saved.quoted_price, Decimal("850.00"))

    def test_custom_enquiry_requires_requirements(self):
        response = self.client.post(
            reverse("birthday:enquiry"),
            {
                "customer_name": "Ravi",
                "email": "ravi@example.com",
                "phone": "+230 5000 1111",
                "event_date": "2027-03-18",
                "venue": str(self.venue.id),
                "package": str(self.custom.id),
                "notes": "Need a custom celebration.",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    def test_inactive_package_cannot_be_booked(self):
        self.starter.is_active = False
        self.starter.save(update_fields=["is_active"])

        response = self.client.get(reverse("birthday:enquiry"), {"package": "starter"})
        self.assertEqual(response.status_code, 400)

    def test_only_birthday_compatible_venues_are_displayed(self):
        other_venue = Venue.objects.create(name="Beach Club", location="Mauritius", price=Decimal("1200.00"))

        response = self.client.get(reverse("birthday:enquiry"), {"package": "professional"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.venue.name)
        self.assertNotContains(response, other_venue.name)
