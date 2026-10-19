from datetime import timedelta
from io import BytesIO
from tempfile import TemporaryDirectory
from decimal import Decimal
from unittest.mock import patch

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone

from authentication.admin_site import superadmin_site
from .models import (
    SeasideBookingRequest,
    SeasidePackage,
    SeasideService,
    SeasideVenue,
)
from .pricing import calculate_estimate


def make_test_image():
    image_bytes = BytesIO()
    Image.new("RGB", (1, 1), color="teal").save(image_bytes, format="PNG")
    return SimpleUploadedFile(
        "catalogue.png",
        image_bytes.getvalue(),
        content_type="image/png",
    )


class SeasideEnquiryFormPageTests(TestCase):
    def test_seaside_page_renders_booking_section_for_visitors(self):
        response = self.client.get(reverse("seaside:seaside"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="seaside-enquiry"')
        self.assertContains(response, "Book your coastal event")

    def test_signed_in_customer_details_prefill_contact_fields(self):
        user = get_user_model().objects.create_user(
            username="seaside-customer",
            email="customer@example.com",
            password="test-password",
            first_name="Tasha",
            last_name="Noor",
            phone="+230 5555 0101",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("seaside:seaside"))

        self.assertContains(response, 'value="Tasha"')
        self.assertContains(response, 'value="Noor"')
        self.assertContains(response, 'value="customer@example.com"')
        self.assertContains(response, 'value="+230 5555 0101"')


def make_customer(**overrides):
    values = {
        "username": "seaside-customer",
        "email": "customer@example.com",
        "password": "SeasidePass123!",
        "first_name": "Tasha",
        "last_name": "Noor",
        "phone": "+230 5555 0101",
    }
    values.update(overrides)
    return get_user_model().objects.create_user(**values)


class SeasideBookingAccessTests(TestCase):
    def test_visitor_sees_sign_in_notice_instead_of_form(self):
        response = self.client.get(reverse("seaside:seaside"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign in to book your event")
        self.assertContains(response, reverse("authentication:register"))
        self.assertNotContains(response, "data-booking-form")
        self.assertContains(response, "Find your perfect seaside setting")

    def test_visitor_and_non_customers_cannot_post_a_booking(self):
        url = reverse("seaside:seaside")
        self.assertEqual(self.client.post(url, {}).status_code, 403)

        staff = make_customer(
            username="seaside-staff",
            email="staff@example.com",
            account_type="staff",
        )
        self.client.force_login(staff)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "data-booking-form")
        self.assertEqual(self.client.post(url, {}).status_code, 403)
        self.assertEqual(SeasideBookingRequest.objects.count(), 0)

        superuser = get_user_model().objects.create_superuser(
            username="seaside-super",
            email="super@example.com",
            password="SeasidePass123!",
            gender="female",
        )
        self.client.force_login(superuser)
        self.assertNotContains(self.client.get(url), "data-booking-form")
        self.assertEqual(self.client.post(url, {}).status_code, 403)

    def test_customer_sees_prefilled_form_with_fixed_event_type(self):
        self.client.force_login(make_customer())
        call_command("seed_seaside_catalog", verbosity=0)

        response = self.client.get(reverse("seaside:seaside"))

        self.assertContains(response, "data-booking-form")
        self.assertContains(response, 'value="Tasha"')
        self.assertContains(response, 'value="Noor"')
        self.assertContains(response, 'value="customer@example.com" readonly')
        self.assertContains(response, 'value="+230 5555 0101"')
        self.assertContains(response, 'id="event-type" value="Seaside" readonly')
        self.assertNotContains(response, 'name="event_type"')
        self.assertNotContains(response, 'name="email"')
        self.assertContains(response, "Submit booking request")

    def test_form_only_offers_active_priced_items(self):
        self.client.force_login(make_customer())
        SeasideVenue.objects.create(
            name="Priced venue", location="x", description="x", price=Decimal("100")
        )
        SeasideVenue.objects.create(name="Unpriced venue", location="x", description="x")
        SeasideVenue.objects.create(
            name="Inactive venue",
            location="x",
            description="x",
            price=Decimal("100"),
            is_active=False,
        )

        response = self.client.get(reverse("seaside:seaside"))
        form_html = response.content.decode().split("data-booking-form", 1)[1]

        self.assertIn("Priced venue (Rs 100)", form_html)
        self.assertNotIn("Unpriced venue (", form_html)
        self.assertNotIn("Inactive venue (", form_html)


class SeasideBookingSubmissionTests(TestCase):
    def setUp(self):
        self.customer = make_customer()
        self.client.force_login(self.customer)
        self.venue = SeasideVenue.objects.create(
            name="Test venue",
            location="x",
            description="x",
            price=Decimal("10000"),
            capacity=100,
        )
        self.package = SeasidePackage.objects.create(
            name="Test package",
            tagline="x",
            price=Decimal("3000"),
            price_basis=SeasidePackage.PriceBasis.PER_GUEST,
            min_guests=10,
            max_guests=80,
        )
        self.styling = SeasideService.objects.create(
            name="Test styling",
            description="x",
            price=Decimal("20000"),
        )
        self.catering = SeasideService.objects.create(
            name="Test catering",
            description="x",
            price=Decimal("1000"),
            price_basis=SeasideService.PriceBasis.PER_GUEST,
        )
        self.url = reverse("seaside:seaside")

    def payload(self, **overrides):
        data = {
            "first_name": "Tasha",
            "last_name": "Noor",
            "phone": "+230 5555 0101",
            "event_name": "Tasha's party",
            "event_date": (timezone.localdate() + timedelta(days=10)).isoformat(),
            "start_time": "15:00",
            "end_time": "20:00",
            "expected_guests": "20",
            "venue": self.venue.pk,
            "package": self.package.pk,
            "optional_services": [self.styling.pk, self.catering.pk],
            "budget": "150000",
            "message": "Sunset please.",
        }
        data.update(overrides)
        return data

    def assertRejected(self, response, field=None):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SeasideBookingRequest.objects.count(), 0)
        if field:
            self.assertIn(field, response.context["form"].errors)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_admins_are_emailed_when_a_request_is_submitted(self):
        from django.core import mail

        get_user_model().objects.create_superuser(
            username="boss", email="boss@example.com", password="pw-12345-xyz"
        )
        self.client.post(self.url, self.payload())

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["boss@example.com"])
        self.assertIn("Tasha Noor", mail.outbox[0].body)
        self.assertIn("/seasidebookingrequest/", mail.outbox[0].body)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_invalid_request_sends_no_admin_email(self):
        from django.core import mail

        get_user_model().objects.create_superuser(
            username="boss", email="boss@example.com", password="pw-12345-xyz"
        )
        self.client.post(self.url, self.payload(end_time="15:00"))
        self.assertEqual(len(mail.outbox), 0)

    def test_email_failure_does_not_block_the_booking(self):
        get_user_model().objects.create_superuser(
            username="boss", email="boss@example.com", password="pw-12345-xyz"
        )
        with patch("seaside.notifications.send_mail", side_effect=OSError("down")):
            response = self.client.post(self.url, self.payload(), follow=True)
        self.assertContains(response, "awaiting approval")
        self.assertEqual(SeasideBookingRequest.objects.count(), 1)

    def test_valid_request_is_saved_with_server_calculated_estimate(self):
        response = self.client.post(self.url, self.payload(), follow=True)

        self.assertContains(response, "awaiting approval")
        booking = SeasideBookingRequest.objects.get()
        # 10,000 + 3,000 x 20 + 20,000 + 1,000 x 20
        self.assertEqual(booking.estimated_total, Decimal("110000.00"))
        self.assertEqual(booking.status, SeasideBookingRequest.Status.PENDING)
        self.assertEqual(booking.customer, self.customer)
        self.assertEqual(booking.event_type, "Seaside")
        self.assertEqual(booking.email, "customer@example.com")
        self.assertEqual(booking.services.count(), 2)
        self.assertEqual(
            [line["subtotal"] for line in booking.price_breakdown],
            ["10000.00", "60000.00", "20000.00", "20000.00"],
        )

    def test_breakdown_snapshot_survives_later_price_changes(self):
        self.client.post(self.url, self.payload())
        self.package.price = Decimal("9999")
        self.package.save()

        booking = SeasideBookingRequest.objects.get()
        self.assertEqual(booking.estimated_total, Decimal("110000.00"))
        self.assertEqual(booking.price_breakdown[1]["unit_price"], "3000.00")

    def test_budget_must_cover_recalculated_total(self):
        self.assertRejected(
            self.client.post(self.url, self.payload(budget="109999.99")), "budget"
        )
        response = self.client.post(self.url, self.payload(budget="110000"))
        self.assertEqual(response.status_code, 302)

    def test_account_email_and_phone_cannot_be_overridden(self):
        self.client.post(
            self.url,
            self.payload(email="someone@else.com", phone="999", first_name=" Sam "),
        )
        booking = SeasideBookingRequest.objects.get()
        self.assertEqual(booking.email, "customer@example.com")
        self.assertEqual(booking.phone, "+230 5555 0101")
        self.assertEqual(booking.first_name, "Sam")

    def test_phone_is_required_and_editable_when_account_has_none(self):
        self.customer.phone = ""
        self.customer.save()
        self.assertRejected(self.client.post(self.url, self.payload(phone="")), "phone")
        self.client.post(self.url, self.payload(phone="+230 5000 0000"))
        self.assertEqual(SeasideBookingRequest.objects.get().phone, "+230 5000 0000")

    def test_required_fields(self):
        for field in (
            "first_name",
            "last_name",
            "event_date",
            "start_time",
            "end_time",
            "expected_guests",
            "venue",
            "package",
            "budget",
        ):
            with self.subTest(field=field):
                self.assertRejected(
                    self.client.post(self.url, self.payload(**{field: ""})), field
                )

    def test_event_name_message_and_services_are_optional(self):
        response = self.client.post(
            self.url,
            self.payload(event_name="", message="", optional_services=[]),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            SeasideBookingRequest.objects.get().estimated_total, Decimal("70000.00")
        )

    def test_invalid_numbers_are_rejected(self):
        for field, value in (
            ("budget", "0"),
            ("budget", "-5"),
            ("budget", "abc"),
            ("budget", "10000001"),
            ("expected_guests", "0"),
            ("expected_guests", "-3"),
            ("expected_guests", "2.5"),
            ("expected_guests", "10001"),
        ):
            with self.subTest(field=field, value=value):
                self.assertRejected(
                    self.client.post(self.url, self.payload(**{field: value})), field
                )

    def test_form_date_picker_blocks_past_dates(self):
        response = self.client.get(self.url)
        today = timezone.localdate().isoformat()
        self.assertContains(response, f'name="event_date" min="{today}"')

    def test_date_rules(self):
        today = timezone.localdate()
        self.assertRejected(
            self.client.post(
                self.url,
                self.payload(event_date=(today - timedelta(days=1)).isoformat()),
            ),
            "event_date",
        )
        self.assertRejected(
            self.client.post(
                self.url,
                self.payload(event_date=(today + timedelta(days=800)).isoformat()),
            ),
            "event_date",
        )

    def test_same_day_start_time_must_be_in_the_future(self):
        today = timezone.localdate()
        noon = timezone.localtime().replace(hour=12, minute=0)
        with patch("seaside.forms.timezone.localtime", return_value=noon):
            self.assertRejected(
                self.client.post(
                    self.url,
                    self.payload(
                        event_date=today.isoformat(),
                        start_time="09:00",
                        end_time="11:00",
                    ),
                ),
                "start_time",
            )
            response = self.client.post(
                self.url,
                self.payload(
                    event_date=today.isoformat(), start_time="14:00", end_time="18:00"
                ),
            )
            self.assertEqual(response.status_code, 302)

    def test_end_time_must_differ_from_start_time(self):
        self.assertRejected(
            self.client.post(self.url, self.payload(end_time="15:00")), "end_time"
        )

    def test_event_lasts_at_most_five_hours_and_ends_by_3am(self):
        for start, end in (
            ("10:00", "15:01"),
            ("20:00", "02:00"),
            ("22:00", "03:01"),
            ("01:00", "04:00"),
        ):
            with self.subTest(start=start, end=end):
                self.assertRejected(
                    self.client.post(
                        self.url, self.payload(start_time=start, end_time=end)
                    ),
                    "end_time",
                )
        for start, end in (("22:00", "03:00"), ("10:00", "15:00"), ("01:00", "03:00")):
            with self.subTest(start=start, end=end):
                response = self.client.post(
                    self.url,
                    self.payload(
                        start_time=start,
                        end_time=end,
                        event_date=(
                            timezone.localdate() + timedelta(days=20 + int(start[:2]))
                        ).isoformat(),
                    ),
                )
                self.assertEqual(response.status_code, 302)

    def test_overnight_event_is_accepted(self):
        response = self.client.post(
            self.url, self.payload(start_time="20:00", end_time="01:00")
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SeasideBookingRequest.objects.count(), 1)

    def test_one_event_per_venue_per_day(self):
        self.client.post(self.url, self.payload(start_time="10:00", end_time="12:00"))
        response = self.client.post(
            self.url, self.payload(start_time="18:00", end_time="22:00")
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("venue", response.context["form"].errors)
        self.assertEqual(SeasideBookingRequest.objects.count(), 1)

    def test_overlapping_request_for_same_venue_is_rejected(self):
        self.client.post(self.url, self.payload(start_time="20:00", end_time="01:00"))
        next_day = (timezone.localdate() + timedelta(days=11)).isoformat()
        for date, start, end in (
            (None, "22:00", "23:00"),
            (next_day, "00:00", "02:00"),
            (None, "18:00", "21:00"),
        ):
            with self.subTest(start=start, end=end):
                overrides = {"start_time": start, "end_time": end}
                if date:
                    overrides["event_date"] = date
                response = self.client.post(self.url, self.payload(**overrides))
                self.assertEqual(response.status_code, 200)
                self.assertIn("venue", response.context["form"].errors)
        self.assertEqual(SeasideBookingRequest.objects.count(), 1)

    def test_back_to_back_and_other_venue_requests_are_allowed(self):
        self.client.post(self.url, self.payload(start_time="20:00", end_time="01:00"))
        next_day = (timezone.localdate() + timedelta(days=11)).isoformat()
        response = self.client.post(
            self.url,
            self.payload(event_date=next_day, start_time="01:00", end_time="03:00"),
        )
        self.assertEqual(response.status_code, 302)
        other = SeasideVenue.objects.create(
            name="Other venue",
            location="x",
            description="x",
            price=Decimal("10000"),
            capacity=100,
        )
        response = self.client.post(
            self.url,
            self.payload(start_time="21:00", end_time="23:00", venue=other.pk),
        )
        self.assertEqual(response.status_code, 302)

    def test_rejected_request_does_not_block_venue(self):
        self.client.post(self.url, self.payload())
        SeasideBookingRequest.objects.update(
            status=SeasideBookingRequest.Status.REJECTED
        )
        response = self.client.post(self.url, self.payload())
        self.assertEqual(response.status_code, 302)

    def test_tampered_selections_are_rejected(self):
        self.venue.is_active = False
        self.venue.save()
        self.assertRejected(self.client.post(self.url, self.payload()), "venue")
        self.venue.is_active = True
        self.venue.save()

        self.styling.price = None
        self.styling.save()
        self.assertRejected(
            self.client.post(self.url, self.payload()), "optional_services"
        )
        self.assertRejected(
            self.client.post(self.url, self.payload(package=99999)), "package"
        )

    def test_guest_limits_are_enforced(self):
        self.assertRejected(
            self.client.post(self.url, self.payload(expected_guests="9")), "package"
        )
        self.assertRejected(
            self.client.post(self.url, self.payload(expected_guests="81")), "package"
        )
        self.package.max_guests = None
        self.package.save()
        self.assertRejected(
            self.client.post(self.url, self.payload(expected_guests="101")), "venue"
        )

    def test_overlong_text_is_rejected(self):
        self.assertRejected(
            self.client.post(self.url, self.payload(message="x" * 1001)), "message"
        )
        self.assertRejected(
            self.client.post(self.url, self.payload(event_name="x" * 121)),
            "event_name",
        )

    def test_database_rejects_equal_start_and_end(self):
        self.client.post(self.url, self.payload())
        booking = SeasideBookingRequest.objects.get()
        booking.end_time = booking.start_time
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                booking.save()

    def test_estimate_uses_decimals_per_basis(self):
        total, lines = calculate_estimate(
            self.venue, self.package, [self.catering], 7
        )
        self.assertEqual(total, Decimal("38000.00"))
        self.assertEqual(lines[2]["quantity"], 7)


class SeasideCatalogTests(TestCase):
    def test_package_and_service_sections_use_seeded_catalogue_with_static_images(self):
        call_command("seed_seaside_catalog", verbosity=0)
        package = SeasidePackage.objects.get(name="Barefoot Gathering")
        package.image = "seaside/images/seaside_venue_pavilion.png"
        package.save(update_fields=("image",))

        response = self.client.get(reverse("seaside:seaside"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Barefoot Gathering")
        self.assertContains(response, "Seaside setup for up to 150 guests")
        self.assertContains(
            response,
            "/static/seaside/images/seaside_venue_pavilion.png",
        )
        self.assertContains(
            response,
            "/static/seaside/images/seaside_services_styling.png",
        )
        self.assertContains(
            response,
            "/static/seaside/images/seaside_services_photography.png",
        )
        self.assertContains(response, "Editorial Coverage")
        self.assertNotContains(response, "From Rs 65,000")

    def test_guest_limits_are_validated(self):
        package = SeasidePackage(
            name="Bad range", tagline="x", min_guests=50, max_guests=10
        )
        with self.assertRaises(ValidationError):
            package.full_clean()
        with self.assertRaises(ValidationError):
            SeasideVenue(
                name="Zero venue", location="x", description="x", capacity=0
            ).full_clean()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SeasidePackage.objects.create(
                    name="Bad range 2", tagline="x", min_guests=50, max_guests=10
                )
        SeasidePackage(
            name="Open ended", tagline="x", min_guests=1, max_guests=None
        ).full_clean()

    def test_seed_sets_default_guest_limits_without_overwriting_admin_changes(self):
        call_command("seed_seaside_catalog", verbosity=0)
        package = SeasidePackage.objects.get(name="Sunset Social")
        self.assertEqual(package.max_guests, 250)
        package.max_guests = 300
        package.save()
        call_command("seed_seaside_catalog", verbosity=0)
        package.refresh_from_db()
        self.assertEqual(package.max_guests, 300)

    def test_negative_price_fails_model_validation(self):
        service = SeasideService(
            name="Negative-price service",
            description="Invalid price test.",
            price=Decimal("-0.01"),
        )

        with self.assertRaises(ValidationError):
            service.full_clean()

    def test_database_rejects_negative_price(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SeasideVenue.objects.create(
                    name="Invalid venue",
                    location="Mauritius",
                    description="Invalid price test.",
                    price=Decimal("-0.01"),
                )

    def test_catalogue_price_may_be_unset_or_zero(self):
        unpriced = SeasidePackage.objects.create(
            name="Unpriced package",
            tagline="Awaiting admin pricing",
        )
        free = SeasideService.objects.create(
            name="Complimentary service",
            description="A free service.",
            price=Decimal("0.00"),
        )

        self.assertIsNone(unpriced.price)
        self.assertEqual(free.price, Decimal("0.00"))

    def test_seed_command_is_idempotent_and_preserves_admin_pricing(self):
        call_command("seed_seaside_catalog", verbosity=0)
        service = SeasideService.objects.get(name="Photography")
        service.price = Decimal("2500.00")
        service.price_basis = SeasideService.PriceBasis.PER_GUEST
        service.is_active = False
        service.save()

        call_command("seed_seaside_catalog", verbosity=0)
        call_command("seed_seaside_catalog", verbosity=0)

        self.assertEqual(SeasideVenue.objects.count(), 3)
        self.assertEqual(SeasidePackage.objects.count(), 3)
        self.assertEqual(SeasideService.objects.count(), 3)
        service.refresh_from_db()
        self.assertEqual(service.price, Decimal("2500.00"))
        self.assertEqual(service.price_basis, SeasideService.PriceBasis.PER_GUEST)
        self.assertFalse(service.is_active)

    def test_only_superadmin_can_open_seaside_catalogue_admin(self):
        customer = get_user_model().objects.create_user(
            username="catalog-customer",
            email="customer@example.com",
            password="test-password",
            gender="female",
        )
        self.client.force_login(customer)
        response = self.client.get(
            reverse("admin:seaside_seasidevenue_changelist")
        )
        self.assertEqual(response.status_code, 302)

        superuser = get_user_model().objects.create_superuser(
            username="catalog-admin",
            email="admin@example.com",
            password="test-password",
            gender="female",
        )
        self.client.force_login(superuser)
        response = self.client.get(
            reverse("admin:seaside_seasidevenue_changelist")
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(superadmin_site.has_permission(response.wsgi_request))

    def test_admin_image_preview_shows_static_images_for_all_catalogue_types(self):
        call_command("seed_seaside_catalog", verbosity=0)
        package = SeasidePackage.objects.get(name="Barefoot Gathering")
        package.image = "seaside/images/seaside_venue_pavilion.png"
        package.save(update_fields=("image",))
        superuser = get_user_model().objects.create_superuser(
            username="static-image-admin",
            email="static-image-admin@example.com",
            password="test-password",
            gender="female",
        )
        self.client.force_login(superuser)

        for model_name, model, item_name in (
            ("seasidevenue", SeasideVenue, "The Glass Pavilion"),
            ("seasidepackage", SeasidePackage, "Barefoot Gathering"),
            ("seasideservice", SeasideService, "Coastal styling"),
        ):
            item = model.objects.get(name=item_name)
            response = self.client.get(
                reverse(
                    f"admin:seaside_{model_name}_change",
                    args=[item.pk],
                )
            )

            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Current image")
            self.assertContains(response, static(item.image))
            self.assertContains(response, "<img")

    def test_superadmin_can_upload_images_for_all_catalogue_types(self):
        superuser = get_user_model().objects.create_superuser(
            username="image-admin",
            email="image-admin@example.com",
            password="test-password",
            gender="female",
        )
        self.client.force_login(superuser)

        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                for model_name in (
                    "seasidevenue",
                    "seasidepackage",
                    "seasideservice",
                ):
                    response = self.client.get(
                        reverse(f"admin:seaside_{model_name}_add")
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertContains(response, 'name="uploaded_image"')

                response = self.client.post(
                    reverse("admin:seaside_seasidevenue_add"),
                    {
                        "name": "Uploaded venue",
                        "location": "North coast",
                        "description": "Venue with an uploaded photograph.",
                        "image": "",
                        "price": "",
                        "price_basis": "per_booking",
                        "is_active": "on",
                        "position": 0,
                        "uploaded_image": make_test_image(),
                    },
                )

                self.assertEqual(response.status_code, 302)
                venue = SeasideVenue.objects.get(name="Uploaded venue")
                self.assertTrue(
                    venue.uploaded_image.name.startswith("seaside/catalog/venues/")
                )
                self.assertTrue(
                    venue.uploaded_image.storage.exists(venue.uploaded_image.name)
                )

                response = self.client.post(
                    reverse("admin:seaside_seasidepackage_add"),
                    {
                        "name": "Uploaded package",
                        "tagline": "Package with a new image",
                        "description": "Package details.",
                        "image": "",
                        "features": "Welcome reception",
                        "min_guests": 1,
                        "max_guests": "",
                        "price": "",
                        "price_basis": "per_booking",
                        "is_featured": "",
                        "is_active": "on",
                        "position": 0,
                        "uploaded_image": make_test_image(),
                    },
                )
                self.assertEqual(response.status_code, 302)

                response = self.client.post(
                    reverse("admin:seaside_seasideservice_add"),
                    {
                        "name": "Uploaded service",
                        "description": "Service with a new image.",
                        "highlights": "Premium\nPersonalized",
                        "image": "",
                        "price": "",
                        "price_basis": "per_booking",
                        "is_active": "on",
                        "position": 0,
                        "uploaded_image": make_test_image(),
                    },
                )
                self.assertEqual(response.status_code, 302)

                package = SeasidePackage.objects.get(name="Uploaded package")
                service = SeasideService.objects.get(name="Uploaded service")
                page = self.client.get(reverse("seaside:seaside"))
                self.assertContains(page, package.uploaded_image.url)
                self.assertContains(page, service.uploaded_image.url)
                self.assertContains(page, venue.uploaded_image.url)
                self.assertContains(page, "Uploaded package")
                self.assertContains(page, "Uploaded service")
