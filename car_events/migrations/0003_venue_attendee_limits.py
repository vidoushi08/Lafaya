from django.db import migrations, models
import django.core.validators
from django.db.models import F, Q


def set_default_venue_limits(apps, schema_editor):
    Venue = apps.get_model("car_events", "Venue")
    limits = {
        "SVICC": (100, 5000),
        "Côte d'Or": (100, 6500),
        "Tribeca Mall": (25, 1000),
    }
    for name, (minimum, maximum) in limits.items():
        Venue.objects.filter(name=name).update(
            min_attendees=minimum,
            max_attendees=maximum,
        )


def clear_default_venue_limits(apps, schema_editor):
    Venue = apps.get_model("car_events", "Venue")
    Venue.objects.filter(
        name__in=("SVICC", "Côte d'Or", "Tribeca Mall")
    ).update(min_attendees=1, max_attendees=None)


class Migration(migrations.Migration):

    dependencies = [
        ("car_events", "0002_careventbookingrequest_alter_eventpackage_options_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="venue",
            name="car_events_venue_capacity_positive",
        ),
        migrations.RenameField(
            model_name="venue",
            old_name="capacity",
            new_name="max_attendees",
        ),
        migrations.AlterField(
            model_name="venue",
            name="max_attendees",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                validators=[django.core.validators.MinValueValidator(1)],
                help_text="Largest number of attendees this venue holds. Leave empty for no limit.",
            ),
        ),
        migrations.AddField(
            model_name="venue",
            name="min_attendees",
            field=models.PositiveIntegerField(
                default=1,
                validators=[django.core.validators.MinValueValidator(1)],
                help_text="Smallest number of attendees this venue accepts.",
            ),
        ),
        migrations.AddConstraint(
            model_name="venue",
            constraint=models.CheckConstraint(
                condition=Q(min_attendees__gte=1),
                name="car_events_venue_min_attendees_positive",
            ),
        ),
        migrations.AddConstraint(
            model_name="venue",
            constraint=models.CheckConstraint(
                condition=Q(max_attendees__isnull=True)
                | Q(max_attendees__gte=F("min_attendees")),
                name="car_events_venue_attendee_range_valid",
            ),
        ),
        migrations.RunPython(
            set_default_venue_limits,
            reverse_code=clear_default_venue_limits,
        ),
    ]
