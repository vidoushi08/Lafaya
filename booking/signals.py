from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import m2m_changed, post_save

from .models import Booking


REQUEST_MODELS = (
    ("birthday", "BirthdayBookingRequest"),
    ("seaside", "SeasideBookingRequest"),
    ("conference", "ConferenceBookingRequest"),
    ("car_events", "CarEventBookingRequest"),
)


def services_summary(request):
    services = getattr(request, "services", None)
    if services is None:
        return ""
    return ", ".join(sorted(service.name for service in services.all()))


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
        "client_name": f"{request.first_name} {request.last_name}".strip(),
        "client_email": request.email,
        "client_phone": request.phone,
        "services_summary": services_summary(request),
    }


def create_or_update_booking(request, content_type):
    snapshot = request_snapshot(request)
    booking = Booking.objects.filter(
        source_content_type=content_type,
        source_object_id=request.pk,
    ).first()

    if booking is None:
        booking = Booking.objects.create(
            source_content_type=content_type,
            source_object_id=request.pk,
            **snapshot,
        )
        return booking, True

    # The booking status is owned by the approval flow, so the request status
    # never overwrites it.
    snapshot.pop("status")
    for field, value in snapshot.items():
        setattr(booking, field, value)
    booking.save(update_fields=(*snapshot.keys(), "updated_at"))
    return booking, False


def connect_request_signals():
    for app_label, model_name in REQUEST_MODELS:
        model = apps.get_model(app_label, model_name)

        def sync_booking(sender, instance, created=False, **kwargs):
            if kwargs.get("raw"):
                return
            content_type = ContentType.objects.get_for_model(sender)
            create_or_update_booking(instance, content_type)

        post_save.connect(
            sync_booking,
            sender=model,
            dispatch_uid=f"booking.sync_{app_label}_{model_name}",
        )

        def sync_booking_services(sender, instance, action, **kwargs):
            if kwargs.get("raw"):
                return
            if action not in ("post_add", "post_remove", "post_clear"):
                return
            content_type = ContentType.objects.get_for_model(instance)
            create_or_update_booking(instance, content_type)

        m2m_changed.connect(
            sync_booking_services,
            sender=model.services.through,
            dispatch_uid=f"booking.sync_services_{app_label}_{model_name}",
        )


def backfill_existing_requests():
    created = 0
    for app_label, model_name in REQUEST_MODELS:
        model = apps.get_model(app_label, model_name)
        content_type = ContentType.objects.get_for_model(model)
        for request in model.objects.select_related(
            "customer", "venue", "package"
        ).iterator():
            _, was_created = create_or_update_booking(request, content_type)
            if was_created:
                created += 1
    return created
