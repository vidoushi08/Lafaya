from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

from booking.models import Booking

from .models import StaffAssignment, StaffTask

DUE_SOON_DAYS = 3

ACTION_LABELS = {
    (StaffTask.Status.PENDING, StaffTask.Status.IN_PROGRESS): "Start",
    (StaffTask.Status.BLOCKED, StaffTask.Status.IN_PROGRESS): "Resume",
    (StaffTask.Status.IN_PROGRESS, StaffTask.Status.COMPLETED): "Mark completed",
    (StaffTask.Status.IN_PROGRESS, StaffTask.Status.BLOCKED): "Report blocked",
}


def tasks_for(user):
    return StaffTask.objects.filter(assignment__staff=user).select_related(
        "assignment__booking"
    )


def assignments_for(user):
    return StaffAssignment.objects.filter(staff=user).select_related("booking")


def task_counts(user):
    today = timezone.localdate()
    counts = tasks_for(user).aggregate(
        total=Count("pk"),
        pending=Count("pk", filter=Q(status=StaffTask.Status.PENDING)),
        in_progress=Count("pk", filter=Q(status=StaffTask.Status.IN_PROGRESS)),
        completed=Count("pk", filter=Q(status=StaffTask.Status.COMPLETED)),
        blocked=Count("pk", filter=Q(status=StaffTask.Status.BLOCKED)),
        due_soon=Count(
            "pk",
            filter=~Q(status=StaffTask.Status.COMPLETED)
            & Q(
                due_date__lte=today + timedelta(days=DUE_SOON_DAYS),
                assignment__booking__status=Booking.Status.CONFIRMED,
            ),
        ),
    )
    return counts


def decorate_tasks(tasks):
    """Attach the update buttons and overdue flag the templates need."""
    today = timezone.localdate()
    decorated = []
    for task in tasks:
        task.actions = [
            (status, ACTION_LABELS[(task.status, status)])
            for status in task.allowed_next_statuses()
        ]
        task.is_overdue = (
            task.status != StaffTask.Status.COMPLETED
            and task.assignment.booking.status == Booking.Status.CONFIRMED
            and task.due_date < today
        )
        decorated.append(task)
    return decorated
