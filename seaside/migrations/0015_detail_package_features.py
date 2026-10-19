from django.db import migrations

NOT_INCLUDED = "Food and drinks not included (add Ocean-to-table catering)"

FEATURES = {
    "Barefoot Gathering": (
        "Seaside setup for up to 150 guests\n"
        "Tables, chairs and relaxed beachside seating\n"
        "Team on site to welcome guests, set up and clear away afterwards\n"
        "Event coordinator to run your timeline on the day\n"
        "Arrival and key moments planned around sunset\n"
        + NOT_INCLUDED
    ),
    "Sunset Social": (
        "Seaside setup for up to 250 guests\n"
        "Tables, chairs and lounge-style seating\n"
        "Sound system, background music and a microphone for speeches\n"
        "Team on site to welcome guests, serve, assist and clear away\n"
        "Event coordinator from setup to close\n"
        + NOT_INCLUDED
    ),
    "Private Island": (
        "Exclusive use of the venue for up to 250 guests, with no other events\n"
        "Entertainment and production planned with you: live music or DJ, stage and lighting\n"
        "Dedicated team to welcome guests, serve, assist and clear away\n"
        "Event coordinator who plans with you beforehand and runs the day\n"
        + NOT_INCLUDED
    ),
}


def set_features(apps, schema_editor):
    SeasidePackage = apps.get_model("seaside", "SeasidePackage")
    for name, features in FEATURES.items():
        SeasidePackage.objects.filter(name=name).update(features=features)


class Migration(migrations.Migration):
    dependencies = [
        ("seaside", "0014_one_event_per_venue_day"),
    ]

    operations = [
        migrations.RunPython(set_features, migrations.RunPython.noop),
    ]
