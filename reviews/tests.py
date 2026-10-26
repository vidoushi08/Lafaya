from datetime import date, time
from decimal import Decimal
import io
import json
from pathlib import Path
import tempfile

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from booking.models import Booking
from .models import Review, ReviewShowcase


class ReviewsPageTests(TestCase):
    def setUp(self):
        self.customer = get_user_model().objects.create_user(
            username="reviewer",
            email="reviewer@example.com",
            password="test-password",
            account_type="customer",
        )
        self.client.force_login(self.customer)
        self.booking = Booking.objects.create(
            customer=self.customer,
            source_content_type=ContentType.objects.get_for_model(self.customer),
            source_object_id=self.customer.pk,
            status=Booking.Status.COMPLETED,
            event_type="Wedding",
            event_name="Garden wedding",
            event_date=date(2025, 6, 1),
            start_time=time(18, 0),
            end_time=time(23, 0),
            guests=40,
            venue_name="Garden",
            package_name="Classic",
            budget=Decimal("10000.00"),
            estimated_total=Decimal("8000.00"),
        )

    def test_reviews_page_renders_and_lists_published_reviews(self):
        Review.objects.create(
            customer=self.customer,
            booking=self.booking,
            rating=5,
            comment="A wonderful celebration.",
            status=Review.Status.PUBLISHED,
        )

        response = self.client.get(reverse("reviews:reviews"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Customer Reviews")
        self.assertContains(response, "Rating Distribution")
        self.assertContains(response, "Write Your Review")
        self.assertContains(response, "reviews/css/reviews.css")
        self.assertContains(response, "reviews/js/reviews.js")
        self.assertContains(response, self.booking.event_name)
        self.assertContains(response, "A wonderful celebration.")

    def test_reviews_page_shows_empty_state_without_published_reviews(self):
        response = self.client.get(reverse("reviews:reviews"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No customer reviews have been published yet.")
        self.assertNotContains(response, "Sample customer")
        self.assertNotContains(response, "Example reviews")

    def test_customer_can_review_own_completed_booking(self):
        response = self.client.post(
            reverse("reviews:reviews"),
            {"booking": self.booking.pk, "rating": 5, "comment": "Wonderful event."},
        )

        self.assertRedirects(response, reverse("reviews:reviews"))
        review = Review.objects.get(booking=self.booking)
        self.assertEqual(review.customer, self.customer)
        self.assertEqual(review.status, Review.Status.PENDING)

    def test_customer_cannot_review_another_customers_completed_booking(self):
        other_customer = get_user_model().objects.create_user(
            username="other", email="other@example.com", password="test-password"
        )
        other_booking = Booking.objects.create(
            customer=other_customer,
            source_content_type=ContentType.objects.get_for_model(other_customer),
            source_object_id=other_customer.pk,
            status=Booking.Status.COMPLETED,
            event_type="Wedding",
            event_date=date(2025, 6, 1),
            start_time=time(18, 0),
            end_time=time(23, 0),
            guests=40,
            venue_name="Garden",
            package_name="Classic",
            budget=Decimal("10000.00"),
            estimated_total=Decimal("8000.00"),
        )

        response = self.client.post(
            reverse("reviews:reviews"),
            {"booking": other_booking.pk, "rating": 5, "comment": "Wonderful event."},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Review.objects.exists())

    def test_customer_cannot_review_a_confirmed_booking(self):
        Booking.objects.filter(pk=self.booking.pk).update(status=Booking.Status.CONFIRMED)

        response = self.client.post(
            reverse("reviews:reviews"),
            {"booking": self.booking.pk, "rating": 5, "comment": "Wonderful event."},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Review.objects.exists())

    def test_customer_can_only_review_booking_once(self):
        Review.objects.create(
            customer=self.customer,
            booking=self.booking,
            rating=4,
            comment="Already reviewed.",
        )

        response = self.client.post(
            reverse("reviews:reviews"),
            {"booking": self.booking.pk, "rating": 5, "comment": "Second attempt."},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Review.objects.filter(booking=self.booking).count(), 1)


class ReviewFixtureTests(TestCase):
    def setUp(self):
        self.customer = get_user_model().objects.create_user(
            username="fixture_reviewer",
            email="private@example.com",
            password="fixture-pass-123",
            account_type="customer",
            first_name="Amina",
        )
        self.booking = Booking.objects.create(
            customer=self.customer,
            source_content_type=ContentType.objects.get_for_model(self.customer),
            source_object_id=self.customer.pk,
            status=Booking.Status.COMPLETED,
            event_type="Wedding",
            event_name="Seaside wedding",
            event_date=date(2025, 6, 1),
            start_time=time(18, 0),
            end_time=time(23, 0),
            guests=40,
            venue_name="Beach",
            package_name="Classic",
            budget=Decimal("10000.00"),
            estimated_total=Decimal("8000.00"),
        )
        Review.objects.create(
            customer=self.customer,
            booking=self.booking,
            rating=5,
            comment="Beautiful day by the sea.",
            status=Review.Status.PUBLISHED,
        )

    def test_export_contains_anonymized_review_without_customer_or_booking_records(self):
        with tempfile.TemporaryDirectory() as output_dir:
            call_command(
                "export_reviews_fixture",
                "--output-dir",
                output_dir,
                stdout=io.StringIO(),
            )
            with open(
                Path(output_dir) / "reviews" / "fixtures" / "reviews_catalogue.json",
                encoding="utf-8",
            ) as fixture_file:
                content = fixture_file.read()

        fixture_objects = json.loads(content)
        self.assertEqual(
            {item["model"] for item in fixture_objects},
            {"reviews.reviewshowcase"},
        )
        self.assertIn("Beautiful day by the sea.", content)
        self.assertNotIn("private@example.com", content)
        self.assertNotIn("Amina", content)
        self.assertNotIn("Seaside wedding", content)

    def test_exported_review_loads_without_importing_or_changing_bookings(self):
        collision_content_type = ContentType.objects.get(
            app_label="car_events",
            model="careventbookingrequest",
        )
        Booking.objects.create(
            customer=self.customer,
            source_content_type=collision_content_type,
            source_object_id=1,
            status=Booking.Status.COMPLETED,
            event_type="Car Event",
            event_date=date(2025, 6, 1),
            start_time=time(18, 0),
            end_time=time(23, 0),
            guests=40,
            venue_name="Venue",
            package_name="Package",
            budget=Decimal("10000.00"),
            estimated_total=Decimal("8000.00"),
        )

        with tempfile.TemporaryDirectory() as output_dir:
            call_command(
                "export_reviews_fixture",
                "--output-dir",
                output_dir,
                stdout=io.StringIO(),
            )
            fixture_path = Path(output_dir) / "reviews" / "fixtures" / "reviews_catalogue.json"
            booking_count = Booking.objects.count()
            review_count = Review.objects.count()
            customer_count = get_user_model().objects.count()

            call_command(
                "load_reviews_fixture",
                str(fixture_path),
                stdout=io.StringIO(),
            )

        self.assertEqual(Booking.objects.count(), booking_count)
        self.assertEqual(Review.objects.count(), review_count)
        self.assertEqual(get_user_model().objects.count(), customer_count)
        self.assertTrue(
            ReviewShowcase.objects.filter(comment="Beautiful day by the sea.").exists()
        )

        self.client.force_login(self.customer)
        response = self.client.get(reverse("reviews:reviews"))
        self.assertContains(response, "Beautiful day by the sea.")
        self.assertContains(response, "Lafaya customer")

    def test_loading_same_review_fixture_is_idempotent(self):
        with tempfile.TemporaryDirectory() as output_dir:
            call_command(
                "export_reviews_fixture",
                "--output-dir",
                output_dir,
                stdout=io.StringIO(),
            )
            fixture_path = Path(output_dir) / "reviews" / "fixtures" / "reviews_catalogue.json"
            for _ in range(2):
                call_command(
                    "load_reviews_fixture",
                    str(fixture_path),
                    stdout=io.StringIO(),
                )

        self.assertEqual(ReviewShowcase.objects.count(), 1)
