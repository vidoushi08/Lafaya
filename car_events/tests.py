from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from authentication.admin_site import superadmin_site
from .models import (
    CarEventBookingRequest,
    EventPackage,
    ExtraService,
    PackageFeature,
    Venue,
)
from .pricing import calculate_estimate


def make_customer(**overrides):
    values = {
        "username": "car-customer",
        "email": "customer@example.com",
        "password": "CarEventPass123!",
        "first_name": "Tasha",
        "last_name": "Noor",
        "phone": "+230 5555 0101",
    }
    values.update(overrides)
    return get_user_model().objects.create_user(**values)


class CarEventPageTests(TestCase):
    def test_visitor_sees_login_notice_and_automotive_catalogue(self):
        response = self.client.get(reverse("car_events:car_events"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Where the road meets the moment.")
        self.assertContains(response, "Sign in to book your event")
        self.assertContains(response, reverse("authentication:register"))
        self.assertNotContains(response, "data-booking-form")

    def test_seeded_catalogue_renders_automotive_content_and_images(self):
        call_command("seed_car_events", verbosity=0)

        response = self.client.get(reverse("car_events:car_events"))

        self.assertContains(response, "SVICC")
        self.assertContains(response, "Starter Meet")
        self.assertContains(response, "Venue sourcing and booking")
        self.assertContains(response, "VIP Experience")
        self.assertContains(
            response,
            "/static/car_events/images/car_venue_svicc.png",
        )
        self.assertContains(
            response,
            "/static/car_events/images/car_services_vip.png",
        )
        self.assertContains(response, "Price on request")

    def test_customer_booking_form_prefills_account_details(self):
        self.client.force_login(make_customer())
        call_command("seed_car_events", verbosity=0)

        response = self.client.get(reverse("car_events:car_events"))

        self.assertContains(response, "data-booking-form")
        self.assertContains(response, 'value="Tasha"')
        self.assertContains(response, 'value="Noor"')
        self.assertContains(response, 'value="customer@example.com" readonly')
        self.assertContains(response, 'value="+230 5555 0101"')
        self.assertContains(response, 'id="event-type" value="Car Event" readonly')
        self.assertContains(response, "Submit booking request")
        self.assertContains(response, "/static/car_events/js/car_events.js")

    def test_non_customers_cannot_submit_booking_requests(self):
        url = reverse("car_events:car_events")
        self.assertEqual(self.client.post(url, {}).status_code, 403)

        staff = make_customer(
            username="car-staff",
            email="staff@example.com",
            account_type="staff",
        )
        self.client.force_login(staff)
        self.assertNotContains(self.client.get(url), "data-booking-form")
        self.assertEqual(self.client.post(url, {}).status_code, 403)
        self.assertEqual(CarEventBookingRequest.objects.count(), 0)

    def test_form_only_offers_active_priced_catalogue_items(self):
        self.client.force_login(make_customer())
        Venue.objects.create(
            name="Priced venue",
            location="x",
            description="x",
            price=Decimal("100"),
        )
        Venue.objects.create(name="Unpriced venue", location="x", description="x")
        Venue.objects.create(
            name="Inactive venue",
            location="x",
            description="x",
            price=Decimal("100"),
            is_active=False,
        )

        response = self.client.get(reverse("car_events:car_events"))
        form_html = response.content.decode().split("data-booking-form", 1)[1]

        self.assertIn("Priced venue (Rs 100)", form_html)
        self.assertNotIn("Unpriced venue (", form_html)
        self.assertNotIn("Inactive venue (", form_html)


class CarEventBookingTests(TestCase):
    def setUp(self):
        self.customer = make_customer()
        self.client.force_login(self.customer)
        self.venue = Venue.objects.create(
            name="Test venue",
            location="x",
            description="x",
            price=Decimal("10000"),
            capacity=100,
        )
        self.package = EventPackage.objects.create(
            name="Test package",
            tagline="x",
            price=Decimal("3000"),
            price_basis=EventPackage.PriceBasis.PER_GUEST,
            min_attendees=10,
            max_attendees=80,
        )
        self.vip = ExtraService.objects.create(
            name="Test VIP service",
            description="x",
            price=Decimal("20000"),
        )
        self.jdm = ExtraService.objects.create(
            name="Test JDM service",
            description="x",
            price=Decimal("1000"),
            price_basis=ExtraService.PriceBasis.PER_GUEST,
        )
        self.url = reverse("car_events:car_events")

    def payload(self, **overrides):
        data = {
            "first_name": "Tasha",
            "last_name": "Noor",
            "phone": "+230 5555 0101",
            "event_name": "Island Motor Meet",
            "event_date": (timezone.localdate() + timedelta(days=10)).isoformat(),
            "start_time": "15:00",
            "end_time": "20:00",
            "expected_attendees": "20",
            "venue": self.venue.pk,
            "package": self.package.pk,
            "optional_services": [self.vip.pk, self.jdm.pk],
            "budget": "150000",
            "message": "Show and shine, please.",
        }
        data.update(overrides)
        return data

    def assert_rejected(self, response, field=None, count=0):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CarEventBookingRequest.objects.count(), count)
        if field:
            self.assertIn(field, response.context["form"].errors)

    def test_request_saves_server_calculated_estimate_and_snapshot(self):
        response = self.client.post(self.url, self.payload())

        self.assertEqual(
            response["Location"],
            f"{reverse('car_events:car_events')}#car-events-enquiry",
        )
        booking = CarEventBookingRequest.objects.get()
        self.assertEqual(booking.status, CarEventBookingRequest.Status.PENDING)
        self.assertEqual(booking.customer, self.customer)
        self.assertEqual(booking.event_type, "Car Event")
        self.assertEqual(booking.email, "customer@example.com")
        self.assertEqual(booking.services.count(), 2)
        self.assertEqual(booking.estimated_total, Decimal("110000.00"))
        self.assertEqual(
            [line["subtotal"] for line in booking.price_breakdown],
            ["10000.00", "60000.00", "20000.00", "20000.00"],
        )

        self.package.price = Decimal("9999")
        self.package.save()
        booking.refresh_from_db()
        self.assertEqual(booking.estimated_total, Decimal("110000.00"))
        self.assertEqual(booking.price_breakdown[1]["unit_price"], "3000.00")

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_admins_are_notified_for_valid_booking(self):
        from django.core import mail

        get_user_model().objects.create_superuser(
            username="car-admin",
            email="admin@example.com",
            password="CarAdminPass123!",
        )

        self.client.post(self.url, self.payload())

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["admin@example.com"])
        self.assertIn("Tasha Noor", mail.outbox[0].body)
        self.assertIn("/careventbookingrequest/", mail.outbox[0].body)

    def test_email_failure_does_not_discard_booking(self):
        get_user_model().objects.create_superuser(
            username="car-admin",
            email="admin@example.com",
            password="CarAdminPass123!",
        )
        with patch(
            "car_events.notifications.send_mail",
            side_effect=OSError("mail service unavailable"),
        ):
            response = self.client.post(self.url, self.payload(), follow=True)

        self.assertContains(response, "awaiting approval")
        self.assertEqual(CarEventBookingRequest.objects.count(), 1)

    def test_customer_email_and_existing_phone_cannot_be_overridden(self):
        self.client.post(
            self.url,
            self.payload(
                email="someone@example.com",
                phone="999",
                first_name=" Sam ",
            ),
        )
        booking = CarEventBookingRequest.objects.get()
        self.assertEqual(booking.email, "customer@example.com")
        self.assertEqual(booking.phone, "+230 5555 0101")
        self.assertEqual(booking.first_name, "Sam")

    def test_phone_is_required_when_account_has_no_phone(self):
        self.customer.phone = ""
        self.customer.save()
        self.assert_rejected(self.client.post(self.url, self.payload(phone="")), "phone")

        self.client.post(self.url, self.payload(phone="+230 5000 0000"))
        self.assertEqual(
            CarEventBookingRequest.objects.get().phone,
            "+230 5000 0000",
        )

    def test_date_duration_and_same_day_rules_are_validated(self):
        today = timezone.localdate()
        self.assert_rejected(
            self.client.post(
                self.url,
                self.payload(event_date=(today - timedelta(days=1)).isoformat()),
            ),
            "event_date",
        )
        self.assert_rejected(
            self.client.post(
                self.url,
                self.payload(
                    event_date=(today + timedelta(days=800)).isoformat(),
                ),
            ),
            "event_date",
        )
        for start, end in (
            ("10:00", "15:01"),
            ("20:00", "02:00"),
            ("22:00", "03:01"),
            ("01:00", "04:00"),
            ("15:00", "15:00"),
        ):
            with self.subTest(start=start, end=end):
                self.assert_rejected(
                    self.client.post(
                        self.url,
                        self.payload(start_time=start, end_time=end),
                    ),
                    "end_time",
                )

    def test_attendee_limits_and_budget_are_enforced(self):
        self.assert_rejected(
            self.client.post(self.url, self.payload(expected_attendees="101")),
            "venue",
        )
        self.assert_rejected(
            self.client.post(self.url, self.payload(expected_attendees="9")),
            "package",
        )
        self.assert_rejected(
            self.client.post(self.url, self.payload(expected_attendees="81")),
            "package",
        )
        self.assert_rejected(
            self.client.post(self.url, self.payload(budget="109999.99")),
            "budget",
        )

    def test_venue_can_have_only_one_active_request_per_day(self):
        self.client.post(self.url, self.payload())
        self.assertEqual(CarEventBookingRequest.objects.count(), 1)

        self.assert_rejected(
            self.client.post(
                self.url,
                self.payload(start_time="10:00", end_time="14:00"),
            ),
            "venue",
            count=1,
        )

        booking = CarEventBookingRequest.objects.get()
        booking.status = CarEventBookingRequest.Status.REJECTED
        booking.save()
        response = self.client.post(
            self.url,
            self.payload(start_time="10:00", end_time="14:00"),
        )
        self.assertEqual(response.status_code, 302)

    def test_inactive_or_unpriced_options_and_bad_values_are_rejected(self):
        self.venue.is_active = False
        self.venue.save()
        self.assert_rejected(self.client.post(self.url, self.payload()), "venue")
        self.venue.is_active = True
        self.venue.save()

        self.vip.price = None
        self.vip.save()
        self.assert_rejected(
            self.client.post(self.url, self.payload()),
            "optional_services",
        )
        self.assert_rejected(
            self.client.post(self.url, self.payload(budget="0")),
            "budget",
        )
        self.assert_rejected(
            self.client.post(self.url, self.payload(expected_attendees="0")),
            "expected_attendees",
        )

    def test_database_rejects_equal_start_and_end(self):
        self.client.post(self.url, self.payload())
        booking = CarEventBookingRequest.objects.get()
        booking.end_time = booking.start_time
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                booking.save()

    def test_estimate_uses_decimal_per_attendee_prices(self):
        total, lines = calculate_estimate(self.venue, self.package, [self.jdm], 7)

        self.assertEqual(total, Decimal("38000.00"))
        self.assertEqual(lines[2]["quantity"], 7)


class CarEventCatalogueTests(TestCase):
    def test_seed_command_is_idempotent_and_preserves_admin_settings(self):
        call_command("seed_car_events", verbosity=0)
        service = ExtraService.objects.get(name="VIP Experience")
        service.price = Decimal("2500.00")
        service.price_basis = ExtraService.PriceBasis.PER_GUEST
        service.is_active = False
        service.save()

        call_command("seed_car_events", verbosity=0)
        call_command("seed_car_events", verbosity=0)

        self.assertEqual(Venue.objects.count(), 3)
        self.assertEqual(EventPackage.objects.count(), 3)
        self.assertEqual(ExtraService.objects.count(), 3)
        self.assertEqual(
            PackageFeature.objects.filter(
                event_package__name__in=(
                    "Starter Meet",
                    "Premium Meet",
                    "Festival Experience",
                )
            ).count(),
            12,
        )
        service.refresh_from_db()
        self.assertEqual(service.price, Decimal("2500.00"))
        self.assertEqual(service.price_basis, ExtraService.PriceBasis.PER_GUEST)
        self.assertFalse(service.is_active)

    def test_guest_capacity_and_package_limits_are_validated(self):
        invalid = EventPackage(
            name="Invalid package",
            tagline="x",
            min_attendees=50,
            max_attendees=10,
        )
        with self.assertRaises(ValidationError):
            invalid.full_clean()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Venue.objects.create(
                    name="Invalid capacity venue",
                    location="x",
                    description="x",
                    capacity=0,
                )

    def test_only_superadmin_can_open_car_event_catalogue_admin(self):
        customer = make_customer(username="catalog-customer")
        self.client.force_login(customer)
        response = self.client.get(reverse("admin:car_events_venue_changelist"))
        self.assertEqual(response.status_code, 302)

        superuser = get_user_model().objects.create_superuser(
            username="catalog-admin",
            email="admin@example.com",
            password="CarAdminPass123!",
        )
        self.client.force_login(superuser)
        response = self.client.get(reverse("admin:car_events_venue_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(superadmin_site.has_permission(response.wsgi_request))
