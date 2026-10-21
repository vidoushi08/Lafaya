from django.db import migrations

REQUEST_MODELS = (
    ("birthday", "BirthdayBookingRequest"),
    ("seaside", "SeasideBookingRequest"),
    ("conference", "ConferenceBookingRequest"),
    ("car_events", "CarEventBookingRequest"),
)


def release_cancelled_requests(apps, schema_editor):
    Booking = apps.get_model("booking", "Booking")
    ContentType = apps.get_model("contenttypes", "ContentType")

    for app_label, model_name in REQUEST_MODELS:
        model = apps.get_model(app_label, model_name)
        content_type = ContentType.objects.filter(
            app_label=app_label, model=model_name.lower()
        ).first()
        if content_type is None:
            continue
        cancelled_ids = Booking.objects.filter(
            status="cancelled",
            source_content_type=content_type,
        ).values_list("source_object_id", flat=True)
        model.objects.filter(pk__in=list(cancelled_ids)).update(status="cancelled")


class Migration(migrations.Migration):

    dependencies = [
        ("booking", "0002_booking_cancelled_at_booking_client_email_and_more"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("birthday", "0002_alter_birthdaybookingrequest_status"),
        ("seaside", "0016_alter_seasidebookingrequest_status"),
        ("conference", "0002_alter_conferencebookingrequest_status"),
        ("car_events", "0003_alter_careventbookingrequest_status"),
    ]

    operations = [
        migrations.RunPython(release_cancelled_requests, migrations.RunPython.noop),
    ]
