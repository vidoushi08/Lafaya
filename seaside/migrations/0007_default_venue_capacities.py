from django.db import migrations

CAPACITIES = {
    "The Glass Pavilion": 100,
    "Sunset Terrace": 150,
    "Oceanfront Villa": 300,
}


def set_capacities(apps, schema_editor):
    SeasideVenue = apps.get_model("seaside", "SeasideVenue")
    for name, capacity in CAPACITIES.items():
        SeasideVenue.objects.filter(name=name, capacity__isnull=True).update(
            capacity=capacity
        )


class Migration(migrations.Migration):
    dependencies = [
        ("seaside", "0006_default_package_guest_limits"),
    ]

    operations = [
        migrations.RunPython(set_capacities, migrations.RunPython.noop),
    ]
