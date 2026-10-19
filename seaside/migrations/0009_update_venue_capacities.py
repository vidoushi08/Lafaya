from django.db import migrations

NEW_CAPACITIES = {
    "The Glass Pavilion": 150,
    "Sunset Terrace": 250,
    "Oceanfront Villa": 350,
}
OLD_CAPACITIES = {
    "The Glass Pavilion": 100,
    "Sunset Terrace": 150,
    "Oceanfront Villa": 300,
}


def apply_capacities(capacities):
    def run(apps, schema_editor):
        SeasideVenue = apps.get_model("seaside", "SeasideVenue")
        for name, capacity in capacities.items():
            SeasideVenue.objects.filter(name=name).update(capacity=capacity)

    return run


class Migration(migrations.Migration):
    dependencies = [
        ("seaside", "0008_booking_request"),
    ]

    operations = [
        migrations.RunPython(
            apply_capacities(NEW_CAPACITIES), apply_capacities(OLD_CAPACITIES)
        ),
    ]
