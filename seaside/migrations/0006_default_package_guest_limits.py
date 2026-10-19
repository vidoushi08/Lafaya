from django.db import migrations

LIMITS = {
    "Barefoot Gathering": 30,
    "Sunset Social": 100,
    "Private Island": 250,
}


def set_default_limits(apps, schema_editor):
    SeasidePackage = apps.get_model("seaside", "SeasidePackage")
    for name, max_guests in LIMITS.items():
        SeasidePackage.objects.filter(name=name, max_guests__isnull=True).update(
            max_guests=max_guests
        )


class Migration(migrations.Migration):
    dependencies = [
        ("seaside", "0005_guest_limits"),
    ]

    operations = [
        migrations.RunPython(set_default_limits, migrations.RunPython.noop),
    ]
