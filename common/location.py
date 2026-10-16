import json

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


CITY_POSTAL_CODES_PATH = settings.BASE_DIR / "static" / "data" / "city_zip.json"


def load_city_postal_codes():
    try:
        with CITY_POSTAL_CODES_PATH.open(encoding="utf-8") as data_file:
            data = json.load(data_file)
    except FileNotFoundError as error:
        raise ImproperlyConfigured(
            f"City/postal-code data was not found at {CITY_POSTAL_CODES_PATH}."
        ) from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ImproperlyConfigured(
            f"City/postal-code data is not valid UTF-8 JSON: {CITY_POSTAL_CODES_PATH}."
        ) from error

    if not isinstance(data, dict):
        raise ImproperlyConfigured("City/postal-code data must be a JSON object.")

    for city, postal_code in data.items():
        if (
            not isinstance(city, str)
            or not city.strip()
            or not isinstance(postal_code, str)
            or not postal_code.strip()
        ):
            raise ImproperlyConfigured(
                "Each city/postal-code entry must contain non-empty strings."
            )

    return dict(sorted(data.items(), key=lambda item: item[0].casefold()))


def load_cities():
    return list(load_city_postal_codes())


def get_postal_code(city):
    return load_city_postal_codes().get(city)