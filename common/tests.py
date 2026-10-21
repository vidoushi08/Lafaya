import io
import json
import tempfile
from pathlib import Path

from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.test import RequestFactory, SimpleTestCase, TestCase

from common.decorators import account_type_required
from common.location import get_postal_code, load_cities, load_city_postal_codes
from common.management.commands.export_catalog_fixtures import CATALOG_MODELS
from car_events.models import Venue
from seaside.models import SeasideVenue


class LocationDataTests(SimpleTestCase):
    def test_city_postal_codes_load_from_global_static_data(self):
        city_postal_codes = load_city_postal_codes()

        self.assertEqual(city_postal_codes["Port Louis"], "11302")
        self.assertTrue(all(isinstance(code, str) for code in city_postal_codes.values()))

    def test_cities_are_sorted(self):
        cities = load_cities()

        self.assertEqual(cities, sorted(cities, key=str.casefold))

    def test_postal_code_lookup_returns_none_for_unknown_city(self):
        self.assertIsNone(get_postal_code("Not a listed city"))


class AccountTypeRequiredTests(SimpleTestCase):
    def setUp(self):
        self.request_factory = RequestFactory()

    def test_superuser_can_access_customer_and_staff_pages(self):
        superuser = get_user_model()(
            username="manager",
            is_active=True,
            is_superuser=True,
        )
        request = self.request_factory.get("/")
        request.user = superuser

        for account_type in ("customer", "staff"):
            with self.subTest(account_type=account_type):
                view = account_type_required(account_type)(
                    lambda request: "allowed"
                )
                self.assertEqual(view(request), "allowed")

    def test_regular_user_must_match_required_account_type(self):
        customer = get_user_model()(
            username="customer",
            is_active=True,
            account_type="customer",
        )
        request = self.request_factory.get("/")
        request.user = customer
        staff_view = account_type_required("staff")(lambda request: "allowed")

        with self.assertRaises(PermissionDenied):
            staff_view(request)

    def test_anonymous_user_is_redirected_to_login(self):
        request = self.request_factory.get("/staff/")
        request.user = AnonymousUser()
        view = account_type_required("staff")(lambda request: "allowed")

        response = view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/authentication/?next=/staff/")


class CatalogFixtureExportTests(TestCase):
    def test_export_contains_only_catalogue_models(self):
        expected_models = {
            "birthday": (
                "BirthdayVenue",
                "BirthdayPackage",
                "BirthdayService",
            ),
            "car_events": (
                "Venue",
                "EventPackage",
                "PackageFeature",
                "ExtraService",
            ),
            "conference": (
                "ConferenceVenue",
                "ConferencePackage",
                "ConferenceService",
            ),
            "seaside": (
                "SeasideVenue",
                "SeasidePackage",
                "SeasideService",
            ),
        }
        self.assertEqual(CATALOG_MODELS, expected_models)

        SeasideVenue.objects.create(
            name="Fixture venue",
            location="Mauritius",
            description="A test catalogue item.",
            price="100.00",
        )
        Venue.objects.create(
            name="Côte d'Or",
            location="Mauritius",
            description="A test car event venue.",
            price="200.00",
        )
        get_user_model().objects.create_user(
            username="private-user",
            email="private@example.com",
            password="test-password",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            call_command(
                "export_catalog_fixtures",
                output_dir=Path(temp_dir),
                stdout=io.StringIO(),
            )
            exported = {}
            for app_label in CATALOG_MODELS:
                fixture_path = (
                    Path(temp_dir)
                    / app_label
                    / "fixtures"
                    / f"{app_label}_catalog.json"
                )
                exported[app_label] = json.loads(
                    fixture_path.read_text(encoding="utf-8")
                )

        self.assertEqual(set(exported), set(CATALOG_MODELS))
        self.assertEqual(
            [item["model"] for item in exported["seaside"]],
            ["seaside.seasidevenue"],
        )
        self.assertEqual(exported["seaside"][0]["fields"]["name"], "Fixture venue")
        self.assertIn(
            "Côte d'Or",
            [item["fields"]["name"] for item in exported["car_events"]],
        )
        self.assertTrue(
            all(
                item["model"].split(".", 1)[0] == app_label
                for app_label, items in exported.items()
                for item in items
            )
        )


class CatalogFixtureLoadTests(TestCase):
    def test_load_catalog_imports_catalogue_rows(self):
        call_command("load_catalog", stdout=io.StringIO())

        self.assertTrue(
            SeasideVenue.objects.filter(name="The Glass Pavilion").exists()
        )
        self.assertTrue(Venue.objects.filter(name="Côte d'Or").exists())