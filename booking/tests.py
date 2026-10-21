from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

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
