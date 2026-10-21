from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save

from .models import Booking


REQUEST_MODELS = (
    ("birthday", "BirthdayBookingRequest"),
    ("seaside", "SeasideBookingRequest"),
    ("conference", "ConferenceBookingRequest"),
    ("car_events", "CarEventBookingRequest"),
)


def request_snapshot(request):
    guests = getattr(request, "expected_guests", None)
    if guests is None:
        guests = request.expected_attendees

    return {
        "customer": request.customer,
        "status": request.status,
        "event_type": request.event_type,
        "event_name": request.event_name,
        "event_date": request.event_date,
        "start_time": request.start_time,
        "end_time": request.end_time,
        "guests": guests,
        "venue_name": request.venue.name,
        "package_name": request.package.name,
        "budget": request.budget,
        "estimated_total": request.estimated_total,
        "message": request.message,
    }


def connect_request_signals():
    for app_label, model_name in REQUEST_MODELS:
        model = apps.get_model(app_label, model_name)

        def sync_booking(sender, instance, created, **kwargs):
            content_type = ContentType.objects.get_for_model(sender)
            if created:
                Booking.objects.create(
                    source_content_type=content_type,
                    source_object_id=instance.pk,
                    **request_snapshot(instance),
                )
                return

            booking = Booking.objects.filter(
                source_content_type=content_type,
                source_object_id=instance.pk,
            ).first()
            if booking is not None:
                snapshot = request_snapshot(instance)
                snapshot.pop("status")
                for field, value in snapshot.items():
                    setattr(booking, field, value)
                booking.save(update_fields=(*snapshot.keys(), "updated_at"))

        post_save.connect(
            sync_booking,
            sender=model,
            dispatch_uid=f"booking.sync_{app_label}_{model_name}",
        )


def backfill_existing_requests():
    for app_label, model_name in REQUEST_MODELS:
        model = apps.get_model(app_label, model_name)
        content_type = ContentType.objects.get_for_model(model)
        for request in model.objects.select_related(
            "customer", "venue", "package"
        ).iterator():
            Booking.objects.get_or_create(
                source_content_type=content_type,
                source_object_id=request.pk,
                defaults=request_snapshot(request),
            )
