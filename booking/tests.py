from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db.models.signals import post_save
from django.test import TestCase
from django.urls import reverse

from payments.models import Payment
from seaside.models import (
    SeasideBookingRequest,
    SeasidePackage,
    SeasideService,
    SeasideVenue,
)

from .models import Booking

class BookingHistoryTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.customer = user_model.objects.create_user(
            username="customer",
            email="customer@example.com",
            password="test-password",
        )
        self.client.force_login(self.customer)
        self.booking = Booking.objects.create(
            customer=self.customer,
            source_content_type=ContentType.objects.get_for_model(user_model),
            source_object_id=self.customer.pk,
            event_type="Birthday",
            event_name="Family celebration",
            event_date=date.today() + timedelta(days=30),
            start_time=time(18, 0),
            end_time=time(21, 0),
            guests=20,
            venue_name="Lagoon venue",
            package_name="Celebration package",
            budget=Decimal("10000.00"),
            estimated_total=Decimal("7000.00"),
        )

    def test_customer_history_shows_only_their_bookings(self):
        response = self.client.get(reverse("booking:booking"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.booking.reference)
        self.assertContains(response, "Family celebration")

    def test_anonymous_customer_history_redirects_to_login(self):
        self.client.logout()
        response = self.client.get(reverse("booking:booking"))
        self.assertRedirects(
            response,
            f"{reverse('authentication:login')}?next={reverse('booking:booking')}",
        )


class BookingStatusTransitionTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.customer = user_model.objects.create_user(
            username="customer",
            email="customer@example.com",
            password="test-password",
        )
        self.booking = Booking.objects.create(
            customer=self.customer,
            source_content_type=ContentType.objects.get_for_model(user_model),
            source_object_id=self.customer.pk,
            event_type="Birthday",
            event_name="Family celebration",
            event_date=date.today() + timedelta(days=30),
            start_time=time(18, 0),
            end_time=time(21, 0),
            guests=20,
            venue_name="Lagoon venue",
            package_name="Celebration package",
            budget=Decimal("10000.00"),
            estimated_total=Decimal("7000.00"),
        )

    def _set_status(self, status):
        Booking.objects.filter(pk=self.booking.pk).update(status=status)
        self.booking.refresh_from_db()

    def test_only_confirmed_bookings_can_be_completed(self):
        with self.assertRaises(ValidationError):
            self.booking.mark_completed()

        self._set_status(Booking.Status.CONFIRMED)
        self.assertTrue(self.booking.mark_completed())

        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.COMPLETED)
        self.assertIsNotNone(self.booking.completed_at)

    def test_completing_a_completed_booking_changes_nothing(self):
        self._set_status(Booking.Status.COMPLETED)

        self.assertFalse(self.booking.mark_completed())

        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.COMPLETED)

    def test_cancelled_booking_cannot_be_completed(self):
        self._set_status(Booking.Status.CANCELLED)

        with self.assertRaises(ValidationError):
            self.booking.mark_completed()

    def test_confirmed_booking_can_be_cancelled(self):
        self._set_status(Booking.Status.CONFIRMED)

        self.assertTrue(self.booking.mark_cancelled())

        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.CANCELLED)
        self.assertIsNotNone(self.booking.cancelled_at)

    def test_rejected_booking_cannot_be_cancelled(self):
        self._set_status(Booking.Status.REJECTED)

        with self.assertRaises(ValidationError):
            self.booking.mark_cancelled()


class BookingPromotionTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.customer = user_model.objects.create_user(
            username="customer",
            email="customer@example.com",
            password="test-password",
        )
        self.venue = SeasideVenue.objects.create(
            name="Lagoon Pavilion",
            location="Grand Baie",
            description="A seaside pavilion.",
            price=Decimal("5000.00"),
        )
        self.package = SeasidePackage.objects.create(
            name="Sunset Plan",
            tagline="Evening events",
            price=Decimal("7000.00"),
            min_guests=10,
            max_guests=100,
        )
        self.service = SeasideService.objects.create(
            name="Photography",
            description="Event photography.",
            price=Decimal("1500.00"),
        )
        self.booking_request = SeasideBookingRequest.objects.create(
            customer=self.customer,
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
            phone="5551234",
            event_name="Seaside wedding",
            event_date=date.today() + timedelta(days=40),
            start_time=time(16, 0),
            end_time=time(22, 0),
            expected_guests=60,
            venue=self.venue,
            package=self.package,
            budget=Decimal("12000.00"),
            estimated_total=Decimal("8500.00"),
        )
        self.booking_request.services.add(self.service)

    def _clear_bookings(self):
        Payment.objects.all().delete()
        Booking.objects.all().delete()

    def test_new_request_creates_booking_with_client_and_services(self):
        booking = Booking.objects.get(source_object_id=self.booking_request.pk)

        self.assertEqual(booking.client_name, "Ada Lovelace")
        self.assertEqual(booking.client_email, "ada@example.com")
        self.assertEqual(booking.client_phone, "5551234")
        self.assertEqual(booking.services_summary, "Photography")
        self.assertEqual(booking.venue_name, "Lagoon Pavilion")
        self.assertEqual(booking.package_name, "Sunset Plan")

    def test_raw_saves_do_not_create_bookings(self):
        self._clear_bookings()

        post_save.send(
            sender=SeasideBookingRequest,
            instance=self.booking_request,
            raw=True,
        )

        self.assertFalse(Booking.objects.exists())

    def test_backfill_command_recreates_missing_bookings(self):
        self._clear_bookings()

        call_command("backfill_bookings", stdout=None, verbosity=0)

        booking = Booking.objects.get(source_object_id=self.booking_request.pk)
        self.assertEqual(booking.client_name, "Ada Lovelace")
        self.assertEqual(booking.services_summary, "Photography")

    def test_backfill_command_keeps_the_existing_booking_status(self):
        booking = Booking.objects.get(source_object_id=self.booking_request.pk)
        booking.status = Booking.Status.APPROVED
        booking.save(update_fields=("status",))

        call_command("backfill_bookings", stdout=None, verbosity=0)

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.APPROVED)
