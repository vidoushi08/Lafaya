from io import BytesIO
from tempfile import TemporaryDirectory
from decimal import Decimal

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.templatetags.static import static
from django.urls import reverse

from authentication.admin_site import superadmin_site
from .models import SeasidePackage, SeasideService, SeasideVenue


def make_test_image():
    image_bytes = BytesIO()
    Image.new("RGB", (1, 1), color="teal").save(image_bytes, format="PNG")
    return SimpleUploadedFile(
        "catalogue.png",
        image_bytes.getvalue(),
        content_type="image/png",
    )


class SeasideEnquiryFormPageTests(TestCase):
    def test_seaside_page_renders_detailed_enquiry_fields(self):
        response = self.client.get(reverse("seaside:seaside"))

        self.assertEqual(response.status_code, 200)
        for field_name in (
            "first_name",
            "last_name",
            "email",
            "phone",
            "event_type",
            "event_name",
            "event_date",
            "start_time",
            "end_time",
            "expected_guests",
            "venue",
            "package",
            "optional_services",
            "budget",
            "message",
        ):
            self.assertContains(response, f'name="{field_name}"')
        self.assertContains(response, "Submit booking request")
        self.assertContains(response, 'id="seaside-enquiry"')

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


class SeasideCatalogTests(TestCase):
    def test_package_and_service_sections_use_seeded_catalogue_with_static_images(self):
        call_command("seed_seaside_catalog", verbosity=0)
        package = SeasidePackage.objects.get(name="Barefoot Gathering")
        package.image = "seaside/images/seaside_venue_pavilion.png"
        package.save(update_fields=("image",))

        response = self.client.get(reverse("seaside:seaside"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Barefoot Gathering")
        self.assertContains(response, "Seaside setup for up to 30 guests")
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
        self.assertEqual(package.max_guests, 100)
        package.max_guests = 120
        package.save()
        call_command("seed_seaside_catalog", verbosity=0)
        package.refresh_from_db()
        self.assertEqual(package.max_guests, 120)

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
