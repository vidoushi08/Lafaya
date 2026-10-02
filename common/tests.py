from django.test import SimpleTestCase

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