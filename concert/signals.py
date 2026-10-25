from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from booking.models import Booking
from booking.signals import request_snapshot
from .models import ConcertBookingRequest


@receiver(post_save, sender=ConcertBookingRequest, dispatch_uid="concert.sync_booking")
def sync_booking(sender, instance, created, raw=False, **kwargs):
    if raw:
        return
    content_type = ContentType.objects.get_for_model(sender)
    if created:
        Booking.objects.create(
            source_content_type=content_type,
            source_object_id=instance.pk,
            **request_snapshot(instance),
        )
    else:
        snapshot = request_snapshot(instance)
        snapshot.pop("status")
        Booking.objects.filter(
            source_content_type=content_type, source_object_id=instance.pk,
        ).update(**snapshot, updated_at=timezone.now())
