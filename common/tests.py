from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, SimpleTestCase

from common.decorators import account_type_required
from common.location import get_postal_code, load_cities, load_city_postal_codes


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