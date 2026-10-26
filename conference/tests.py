from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from authentication.admin_site import superadmin_site

from .models import (
    ConferenceBookingRequest,
    ConferencePackage,
    ConferenceService,
    ConferenceVenue,
)


class ConferenceAccessTests(TestCase):
    def test_anonymous_user_sees_customer_access_notice(self):
        response = self.client.get(reverse("conference:conference"))

        self.assertContains(response, "Sign in to plan your event")
        self.assertContains(response, "Create an account")
        self.assertNotContains(response, "data-booking-form")

    def test_customer_sees_booking_form(self):
        user = get_user_model().objects.create_user(
            username="conference-customer",
            email="conference-customer@example.com",
            password="test-password",
            account_type="customer",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("conference:conference"))

        self.assertContains(response, "data-booking-form")
        self.assertNotContains(response, "Sign in to plan your event")

    def test_staff_user_sees_customer_access_notice(self):
        user = get_user_model().objects.create_user(
            username="conference-staff",
            email="conference-staff@example.com",
            password="test-password",
            account_type="staff",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("conference:conference"))

        self.assertContains(response, "customer accounts")
        self.assertNotContains(response, "data-booking-form")


class ConferenceBookingTests(TestCase):
    def setUp(self):
        self.customer = get_user_model().objects.create_user(
            username="conf-booker",
            email="booker@example.com",
            account_type="customer",
            first_name="Clara",
            last_name="Mark",
        )
        self.client.force_login(self.customer)
        self.venue = ConferenceVenue.objects.create(
            name="Hall", location="x", description="x",
            price=Decimal("50000"), capacity=300,
        )
        self.package = ConferencePackage.objects.create(
            name="Pro", tagline="x", price=Decimal("2000"),
            price_basis=ConferencePackage.PriceBasis.PER_GUEST,
            min_guests=10, max_guests=200,
        )
        self.service = ConferenceService.objects.create(
            name="Catering", description="x", price=Decimal("500"),
            price_basis=ConferenceService.PriceBasis.PER_GUEST,
        )
        self.url = reverse("conference:conference")

    def payload(self, **overrides):
        data = {
            "first_name": "Clara",
            "last_name": "Mark",
            "phone": "+230 5555 0101",
            "event_name": "Summit",
            "event_date": (timezone.localdate() + timedelta(days=10)).isoformat(),
            "start_time": "09:00",
            "end_time": "15:00",
            "expected_guests": "20",
            "venue": self.venue.pk,
            "package": self.package.pk,
            "optional_services": [self.service.pk],
            "budget": "200000",
            "message": "Hello",
        }
        data.update(overrides)
        return data

    def test_visitor_and_staff_cannot_post(self):
        self.client.logout()
        self.assertEqual(self.client.post(self.url, self.payload()).status_code, 403)
        staff = get_user_model().objects.create_user(
            username="conf-staff", account_type="staff"
        )
        self.client.force_login(staff)
        self.assertEqual(self.client.post(self.url, self.payload()).status_code, 403)
        self.assertEqual(ConferenceBookingRequest.objects.count(), 0)

    def test_page_lists_catalogue_and_only_bookable_options(self):
        ConferenceVenue.objects.create(name="Unpriced", location="x", description="x")
        response = self.client.get(self.url)
        self.assertContains(response, "Hall")
        self.assertEqual(list(response.context["bookable_venues"]), [self.venue])

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_valid_request_is_saved_with_estimate_and_admin_emailed(self):
        get_user_model().objects.create_superuser(
            username="boss", email="boss@example.com", password="x-Pass-123"
        )
        response = self.client.post(self.url, self.payload())
        self.assertEqual(response.status_code, 302)
        booking = ConferenceBookingRequest.objects.get()
        # 50000 + 2000*20 + 500*20
        self.assertEqual(booking.estimated_total, Decimal("100000.00"))
        self.assertEqual(booking.email, "booker@example.com")
        self.assertEqual(booking.status, "pending")
        self.assertEqual(list(booking.services.all()), [self.service])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/conferencebookingrequest/", mail.outbox[0].body)

    def test_email_failure_does_not_block_booking(self):
        get_user_model().objects.create_superuser(
            username="boss", email="boss@example.com", password="x-Pass-123"
        )
        with patch("conference.notifications.send_mail", side_effect=OSError):
            response = self.client.post(self.url, self.payload())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ConferenceBookingRequest.objects.count(), 1)

    def assertRejected(self, response, field):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ConferenceBookingRequest.objects.count(), 0)
        self.assertIn(field, response.context["form"].errors)

    def test_budget_must_cover_total(self):
        self.assertRejected(self.client.post(self.url, self.payload(budget="1000")), "budget")

    def test_guest_limits(self):
        self.assertRejected(
            self.client.post(self.url, self.payload(expected_guests="5")), "package"
        )
        self.assertRejected(
            self.client.post(self.url, self.payload(expected_guests="250")), "package"
        )
        self.venue.capacity = 10
        self.venue.save()
        self.assertRejected(self.client.post(self.url, self.payload()), "venue")

    def test_date_and_time_rules(self):
        past = (timezone.localdate() - timedelta(days=1)).isoformat()
        self.assertRejected(self.client.post(self.url, self.payload(event_date=past)), "event_date")
        self.assertRejected(
            self.client.post(self.url, self.payload(end_time="09:00")), "end_time"
        )
        self.assertRejected(
            self.client.post(self.url, self.payload(start_time="09:00", end_time="15:01")),
            "end_time",
        )

    def test_overlapping_booking_for_same_venue_is_rejected(self):
        self.assertEqual(self.client.post(self.url, self.payload()).status_code, 302)
        response = self.client.post(self.url, self.payload(start_time="10:00", end_time="12:00"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("venue", response.context["form"].errors)
        self.assertEqual(ConferenceBookingRequest.objects.count(), 1)

    def test_rejected_request_frees_the_venue(self):
        self.client.post(self.url, self.payload())
        ConferenceBookingRequest.objects.update(status="rejected")
        self.assertEqual(self.client.post(self.url, self.payload()).status_code, 302)

    def test_tampered_selection_is_rejected(self):
        unpriced = ConferenceVenue.objects.create(name="Nope", location="x", description="x")
        self.assertRejected(
            self.client.post(self.url, self.payload(venue=unpriced.pk)), "venue"
        )

    def test_account_phone_cannot_be_overridden(self):
        self.customer.phone = "+230 1111 2222"
        self.customer.save()
        self.client.post(self.url, self.payload(phone="999"))
        self.assertEqual(ConferenceBookingRequest.objects.get().phone, "+230 1111 2222")

    def test_database_blocks_duplicate_active_venue_day(self):
        self.client.post(self.url, self.payload())
        booking = ConferenceBookingRequest.objects.get()
        with self.assertRaises(IntegrityError), transaction.atomic():
            ConferenceBookingRequest.objects.create(
                customer=self.customer, first_name="a", last_name="b",
                email="a@b.com", phone="1", event_date=booking.event_date,
                start_time="01:00", end_time="02:00", expected_guests=20,
                venue=self.venue, package=self.package, budget=1, estimated_total=0,
            )


class ConferenceCatalogueTests(TestCase):
    def test_seed_is_idempotent_and_preserves_admin_changes(self):
        call_command("seed_conference_catalog", verbosity=0)
        self.assertEqual(ConferenceVenue.objects.count(), 3)
        self.assertEqual(ConferencePackage.objects.count(), 3)
        self.assertEqual(ConferenceService.objects.count(), 3)
        package = ConferencePackage.objects.get(name="Starter Plan")
        self.assertEqual(package.price, Decimal("80000"))
        package.price = Decimal("99000")
        package.max_guests = 60
        package.is_active = False
        package.save()
        call_command("seed_conference_catalog", verbosity=0)
        package.refresh_from_db()
        self.assertEqual(
            (package.price, package.max_guests, package.is_active),
            (Decimal("99000"), 60, False),
        )
        self.assertEqual(ConferencePackage.objects.count(), 3)

    def test_conference_models_are_registered_on_superadmin_site_only(self):
        for model in (
            ConferenceVenue, ConferencePackage, ConferenceService, ConferenceBookingRequest,
        ):
            self.assertIn(model, superadmin_site._registry)

    def test_negative_price_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ConferenceService.objects.create(
                name="Bad", description="x", price=Decimal("-1")
            )
