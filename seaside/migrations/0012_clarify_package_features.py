from django.db import migrations

NOT_INCLUDED = "Food and drinks not included (add Ocean-to-table catering)"

FEATURES = {
    "Barefoot Gathering": (
        "Seaside setup for up to 150 guests\n"
        "On-site service team to look after your event\n"
        "Event coordination and a planned sunset timeline\n"
        + NOT_INCLUDED
    ),
    "Sunset Social": (
        "Seaside setup for up to 250 guests\n"
        "Music and sound system\n"
        "Full service team and event coordination\n"
        + NOT_INCLUDED
    ),
    "Private Island": (
        "Exclusive use of the venue for up to 250 guests\n"
        "Custom entertainment and production\n"
        "Full service team and event coordination\n"
        + NOT_INCLUDED
    ),
}


def set_features(apps, schema_editor):
    SeasidePackage = apps.get_model("seaside", "SeasidePackage")
    for name, features in FEATURES.items():
        SeasidePackage.objects.filter(name=name).update(features=features)


class Migration(migrations.Migration):
    dependencies = [
        ("seaside", "0011_lower_package_prices"),
    ]

    operations = [
        migrations.RunPython(set_features, migrations.RunPython.noop),
    ]
