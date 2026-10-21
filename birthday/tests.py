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
    BirthdayBookingRequest,
    BirthdayPackage,
    BirthdayService,
    BirthdayVenue,
)
from .pricing import calculate_estimate


def make_customer(**overrides):
    values = {
        "username": "birthday-customer",
        "email": "customer@example.com",
        "password": "BirthdayPass123!",
        "first_name": "Maya",
        "last_name": "Noor",
        "phone": "+230 5555 0101",
        "gender": "female",
    }
    values.update(overrides)
    return get_user_model().objects.create_user(**values)


class BirthdayPageTests(TestCase):
    def test_visitors_see_birthday_catalogue_and_sign_in_notice(self):
        call_command("seed_birthday_catalog", verbosity=0)
        response = self.client.get(reverse("birthday:birthday"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Make their day unforgettable.")
        self.assertContains(response, "Grand Ballroom")
        self.assertContains(response, "Little Moments")
        self.assertContains(response, "Birthday styling")
        self.assertContains(response, "/static/birthday/images/birthday_venue_ballroom.png")
        self.assertContains(response, "Sign in to book your event")
        self.assertContains(response, reverse("authentication:register"))
        self.assertNotContains(response, "data-booking-form")

    def test_customer_form_prefills_account_details_and_loads_script(self):
        customer = make_customer()
        self.client.force_login(customer)
        call_command("seed_birthday_catalog", verbosity=0)

        response = self.client.get(reverse("birthday:birthday"))

        self.assertContains(response, "data-booking-form")
        self.assertContains(response, 'value="Maya"')
        self.assertContains(response, 'value="Noor"')
        self.assertContains(response, 'value="customer@example.com" readonly')
        self.assertContains(response, 'value="+230 5555 0101"')
        self.assertContains(response, 'id="event-type" value="Birthday" readonly')
        self.assertContains(response, "/static/birthday/js/birthday.js")
        self.assertContains(response, "Submit booking request")

    def test_non_customers_cannot_make_booking_requests(self):
        url = reverse("birthday:birthday")
        self.assertEqual(self.client.post(url, {}).status_code, 403)

        staff = make_customer(
            username="birthday-staff",
            email="staff@example.com",
            account_type="staff",
        )
        self.client.force_login(staff)
        self.assertNotContains(self.client.get(url), "data-booking-form")
        self.assertEqual(self.client.post(url, {}).status_code, 403)
        self.assertEqual(BirthdayBookingRequest.objects.count(), 0)

    def test_form_only_offers_active_priced_items(self):
        self.client.force_login(make_customer())
        BirthdayVenue.objects.create(
            name="Priced venue",
            location="x",
            description="x",
            price=Decimal("100"),
        )
        BirthdayVenue.objects.create(
            name="Unpriced venue",
            location="x",
            description="x",
        )
        BirthdayVenue.objects.create(
            name="Inactive venue",
            location="x",
            description="x",
            price=Decimal("100"),
            is_active=False,
        )

        response = self.client.get(reverse("birthday:birthday"))
        form_html = response.content.decode().split("data-booking-form", 1)[1]

        self.assertIn("Priced venue (Rs 100)", form_html)
        self.assertNotIn("Unpriced venue (", form_html)
        self.assertNotIn("Inactive venue (", form_html)


class BirthdayBookingTests(TestCase):
    def setUp(self):
        self.customer = make_customer()
        self.client.force_login(self.customer)
        self.venue = BirthdayVenue.objects.create(
            name="Test venue",
            location="x",
            description="x",
            price=Decimal("10000"),
            capacity=100,
        )
        self.package = BirthdayPackage.objects.create(
            name="Test package",
            tagline="x",
            price=Decimal("3000"),
            price_basis=BirthdayPackage.PriceBasis.PER_GUEST,
            min_guests=10,
            max_guests=80,
        )
        self.styling = BirthdayService.objects.create(
            name="Test styling",
            description="x",
            price=Decimal("20000"),
        )
        self.gastronomy = BirthdayService.objects.create(
            name="Test gastronomy",
            description="x",
            price=Decimal("1000"),
            price_basis=BirthdayService.PriceBasis.PER_GUEST,
        )
        self.url = reverse("birthday:birthday")

    def payload(self, **overrides):
        data = {
            "first_name": "Maya",
            "last_name": "Noor",
            "phone": "+230 5555 0101",
            "event_name": "Maya's birthday",
            "event_date": (timezone.localdate() + timedelta(days=10)).isoformat(),
            "start_time": "15:00",
            "end_time": "20:00",
            "expected_guests": "20",
            "venue": self.venue.pk,
            "package": self.package.pk,
            "optional_services": [self.styling.pk, self.gastronomy.pk],
            "budget": "150000",
            "message": "A joyful family celebration.",
        }
        data.update(overrides)
        return data

    def assert_rejected(self, response, field=None, count=0):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(BirthdayBookingRequest.objects.count(), count)
        if field:
            self.assertIn(field, response.context["form"].errors)

    def test_request_saves_pending_booking_and_server_calculated_price_snapshot(self):
        response = self.client.post(self.url, self.payload())

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            f"{reverse('birthday:birthday')}#birthday-enquiry",
        )
        booking = BirthdayBookingRequest.objects.get()
        self.assertEqual(booking.status, BirthdayBookingRequest.Status.PENDING)
        self.assertEqual(booking.customer, self.customer)
        self.assertEqual(booking.event_type, "Birthday")
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
    def test_admin_is_notified_for_valid_booking(self):
        from django.core import mail

        get_user_model().objects.create_superuser(
            username="birthday-admin",
            email="admin@example.com",
            password="BirthdayAdmin123!",
        )

        self.client.post(self.url, self.payload())

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["admin@example.com"])
        self.assertIn("Maya Noor", mail.outbox[0].body)
        self.assertIn("/birthdaybookingrequest/", mail.outbox[0].body)

    def test_email_failure_does_not_discard_booking(self):
        with patch(
            "birthday.notifications.send_mail",
            side_effect=OSError("mail service unavailable"),
        ):
            response = self.client.post(self.url, self.payload(), follow=True)

        self.assertContains(response, "awaiting approval")
        self.assertEqual(BirthdayBookingRequest.objects.count(), 1)

    def test_account_email_and_existing_phone_cannot_be_overridden(self):
        self.client.post(
            self.url,
            self.payload(
                email="someone@example.com",
                phone="999",
                first_name=" Sam ",
            ),
        )
        booking = BirthdayBookingRequest.objects.get()
        self.assertEqual(booking.email, "customer@example.com")
        self.assertEqual(booking.phone, "+230 5555 0101")
        self.assertEqual(booking.first_name, "Sam")

    def test_phone_is_required_when_account_has_no_phone(self):
        self.customer.phone = ""
        self.customer.save()
        self.assert_rejected(self.client.post(self.url, self.payload(phone="")), "phone")

        self.client.post(self.url, self.payload(phone="+230 5000 0000"))
        self.assertEqual(
            BirthdayBookingRequest.objects.get().phone,
            "+230 5000 0000",
        )

    def test_date_time_and_attendee_rules_are_enforced(self):
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
                self.payload(event_date=(today + timedelta(days=800)).isoformat()),
            ),
            "event_date",
        )
        self.assert_rejected(
            self.client.post(
                self.url,
                self.payload(start_time="15:00", end_time="15:00"),
            ),
            "end_time",
        )
        self.assert_rejected(
            self.client.post(
                self.url,
                self.payload(start_time="10:00", end_time="15:01"),
            ),
            "end_time",
        )
        self.assert_rejected(
            self.client.post(self.url, self.payload(expected_guests="101")),
            "venue",
        )
        self.assert_rejected(
            self.client.post(self.url, self.payload(expected_guests="9")),
            "package",
        )
        self.assert_rejected(
            self.client.post(self.url, self.payload(expected_guests="81")),
            "package",
        )

    def test_budget_and_unavailable_options_are_rejected(self):
        self.assert_rejected(
            self.client.post(self.url, self.payload(budget="109999.99")),
            "budget",
        )
        self.assert_rejected(
            self.client.post(self.url, self.payload(budget="0")),
            "budget",
        )
        self.styling.price = None
        self.styling.save()
        self.assert_rejected(
            self.client.post(self.url, self.payload()),
            "optional_services",
        )

    def test_one_active_booking_per_venue_and_day(self):
        self.client.post(self.url, self.payload())
        self.assertEqual(BirthdayBookingRequest.objects.count(), 1)
        self.assert_rejected(
            self.client.post(
                self.url,
                self.payload(start_time="10:00", end_time="14:00"),
            ),
            "venue",
            count=1,
        )

        booking = BirthdayBookingRequest.objects.get()
        booking.status = BirthdayBookingRequest.Status.REJECTED
        booking.save()
        self.assertEqual(
            self.client.post(
                self.url,
                self.payload(start_time="10:00", end_time="14:00"),
            ).status_code,
            302,
        )

    def test_database_rejects_equal_start_and_end(self):
        self.client.post(self.url, self.payload())
        booking = BirthdayBookingRequest.objects.get()
        booking.end_time = booking.start_time
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                booking.save()

    def test_estimate_uses_decimal_prices_per_guest(self):
        total, lines = calculate_estimate(
            self.venue,
            self.package,
            [self.gastronomy],
            7,
        )

        self.assertEqual(total, Decimal("38000.00"))
        self.assertEqual(lines[2]["quantity"], 7)


class BirthdayCatalogueTests(TestCase):
    def test_seed_is_idempotent_and_preserves_admin_prices_and_limits(self):
        call_command("seed_birthday_catalog", verbosity=0)
        venue = BirthdayVenue.objects.get(name="Grand Ballroom")
        package = BirthdayPackage.objects.get(name="Signature Celebration")
        service = BirthdayService.objects.get(name="Birthday styling")
        venue.price = Decimal("50000")
        venue.capacity = 350
        venue.save()
        package.price = Decimal("25000")
        package.max_guests = 175
        package.save()
        service.price = Decimal("5000")
        service.is_active = False
        service.save()

        call_command("seed_birthday_catalog", verbosity=0)
        call_command("seed_birthday_catalog", verbosity=0)

        self.assertEqual(BirthdayVenue.objects.count(), 3)
        self.assertEqual(BirthdayPackage.objects.count(), 3)
        self.assertEqual(BirthdayService.objects.count(), 3)
        venue.refresh_from_db()
        package.refresh_from_db()
        service.refresh_from_db()
        self.assertEqual(venue.price, Decimal("50000"))
        self.assertEqual(venue.capacity, 350)
        self.assertEqual(package.price, Decimal("25000"))
        self.assertEqual(package.max_guests, 175)
        self.assertEqual(service.price, Decimal("5000"))
        self.assertFalse(service.is_active)

    def test_package_guest_limits_are_validated(self):
        package = BirthdayPackage(
            name="Invalid package",
            tagline="x",
            min_guests=50,
            max_guests=10,
        )
        with self.assertRaises(ValidationError):
            package.full_clean()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                BirthdayVenue.objects.create(
                    name="Invalid capacity venue",
                    location="x",
                    description="x",
                    capacity=0,
                )

    def test_only_superadmin_can_open_catalogue_admin(self):
        customer = make_customer(username="birthday-catalog-customer")
        self.client.force_login(customer)
        response = self.client.get(reverse("admin:birthday_birthdayvenue_changelist"))
        self.assertEqual(response.status_code, 302)

        superuser = get_user_model().objects.create_superuser(
            username="birthday-catalog-admin",
            email="admin@example.com",
            password="BirthdayAdmin123!",
        )
        self.client.force_login(superuser)
        response = self.client.get(reverse("admin:birthday_birthdayvenue_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(superadmin_site.has_permission(response.wsgi_request))
