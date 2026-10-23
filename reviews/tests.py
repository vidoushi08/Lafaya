from datetime import date, time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from booking.models import Booking

from .models import Review


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
        response = self.client.get(reverse("reviews:reviews"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Customer Reviews")
        self.assertContains(response, "Rating Distribution")
        self.assertContains(response, "Write Your Review")
        self.assertContains(response, "reviews/css/reviews.css")
        self.assertContains(response, "reviews/js/reviews.js")
        self.assertContains(response, self.booking.event_name)

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
