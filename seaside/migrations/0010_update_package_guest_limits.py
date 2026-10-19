from django.db import migrations

NEW_LIMITS = {
    "Barefoot Gathering": 150,
    "Sunset Social": 250,
    "Private Island": 250,
}
OLD_LIMITS = {
    "Barefoot Gathering": 30,
    "Sunset Social": 100,
    "Private Island": 250,
}


def apply_limits(limits):
    def run(apps, schema_editor):
        SeasidePackage = apps.get_model("seaside", "SeasidePackage")
        for name, max_guests in limits.items():
            SeasidePackage.objects.filter(name=name).update(max_guests=max_guests)

    return run


class Migration(migrations.Migration):
    dependencies = [
        ("seaside", "0009_update_venue_capacities"),
    ]

    operations = [
        migrations.RunPython(apply_limits(NEW_LIMITS), apply_limits(OLD_LIMITS)),
    ]
