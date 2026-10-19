from decimal import Decimal

from django.db import migrations

NEW_PRICES = {
    "Barefoot Gathering": Decimal("2000.00"),
    "Sunset Social": Decimal("2500.00"),
    "Private Island": Decimal("3000.00"),
}
OLD_PRICES = {
    "Barefoot Gathering": Decimal("3000.00"),
    "Sunset Social": Decimal("4000.00"),
    "Private Island": Decimal("6500.00"),
}


def apply_prices(prices):
    def run(apps, schema_editor):
        SeasidePackage = apps.get_model("seaside", "SeasidePackage")
        for name, price in prices.items():
            SeasidePackage.objects.filter(name=name).update(price=price)

    return run


class Migration(migrations.Migration):
    dependencies = [
        ("seaside", "0010_update_package_guest_limits"),
    ]

    operations = [
        migrations.RunPython(apply_prices(NEW_PRICES), apply_prices(OLD_PRICES)),
    ]
