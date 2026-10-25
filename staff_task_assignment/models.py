from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from booking.models import Booking

def _minutes_range(start, end):
    start_minutes = start.hour * 60 + start.minute
    end_minutes = end.hour * 60 + end.minute
    if end_minutes <= start_minutes:
        # An event ending at or before its start time runs past midnight.
        end_minutes += 24 * 60
    return start_minutes, end_minutes


class StaffAssignment(models.Model):
    booking = models.ForeignKey(
        Booking,
        on_delete=models.PROTECT,
        related_name="staff_assignments",
    )
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="staff_assignments",
        limit_choices_to={
            "account_type": "staff",
            "is_active": True,
            "is_superuser": False,
        },
    )
    role = models.CharField(
        max_length=120,
        help_text="For example Decorator, Audio Lead or Catering Coordinator.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name="created_staff_assignments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["booking__event_date", "booking__start_time", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=("booking", "staff"),
                name="staff_assignment_unique_staff_per_booking",
            ),
        ]

    def __str__(self):
        return f"{self.staff} - {self.role} ({self.booking.reference})"

    def validate_assignable(self):
        errors = []
        if self.booking_id is not None:
            if self.booking.status != Booking.Status.CONFIRMED:
                errors.append("Staff can only be assigned to confirmed bookings.")
        if self.staff_id is not None:
            staff = self.staff
            if (
                staff.is_superuser
                or staff.account_type != staff.AccountType.STAFF
                or not staff.is_active
            ):
                errors.append("Choose an active staff account.")
        if errors:
            raise ValidationError(errors)

    def clean(self):
        super().clean()
        # Existing assignments stay editable after the event closes, so the
        # confirmed-booking gate applies only when an assignment is created.
        if self._state.adding:
            self.validate_assignable()

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.validate_assignable()
        super().save(*args, **kwargs)

    def conflicting_assignments(self):
        """Other confirmed assignments for this staff member that overlap in time."""
        if self.booking_id is None or self.staff_id is None:
            return []

        start, end = _minutes_range(self.booking.start_time, self.booking.end_time)
        candidates = (
            StaffAssignment.objects.filter(
                staff_id=self.staff_id,
                booking__event_date=self.booking.event_date,
                booking__status=Booking.Status.CONFIRMED,
            )
            .exclude(booking_id=self.booking_id)
            .select_related("booking")
        )
        conflicts = []
        for other in candidates:
            other_start, other_end = _minutes_range(
                other.booking.start_time, other.booking.end_time
            )
            if other_start < end and other_end > start:
                conflicts.append(other)
        return conflicts


class StaffTask(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        BLOCKED = "blocked", "Blocked"

    ALLOWED_TRANSITIONS = {
        Status.PENDING: (Status.IN_PROGRESS,),
        Status.IN_PROGRESS: (Status.COMPLETED, Status.BLOCKED),
        Status.BLOCKED: (Status.IN_PROGRESS,),
        Status.COMPLETED: (),
    }

    assignment = models.ForeignKey(
        StaffAssignment,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    priority = models.CharField(
        max_length=8,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    due_date = models.DateField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_date", "-created_at"]
        indexes = [models.Index(fields=("status", "due_date"))]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if (
            self._state.adding
            and self.assignment_id is not None
            and self.assignment.booking.status != Booking.Status.CONFIRMED
        ):
            raise ValidationError("Tasks can only be added to confirmed bookings.")

    def allowed_next_statuses(self):
        if self.assignment.booking.status != Booking.Status.CONFIRMED:
            return ()
        return self.ALLOWED_TRANSITIONS[self.status]

    @transaction.atomic
    def transition_to(self, new_status):
        task = (
            type(self)
            .objects.select_for_update()
            .select_related("assignment__booking")
            .get(pk=self.pk)
        )
        if task.assignment.booking.status != Booking.Status.CONFIRMED:
            raise ValidationError(
                "This event is closed, so its tasks can no longer be changed."
            )
        if new_status not in task.ALLOWED_TRANSITIONS.get(task.status, ()):
            raise ValidationError(
                f"A {task.get_status_display().lower()} task cannot be moved to "
                f"{dict(self.Status.choices).get(new_status, new_status)}."
            )

        task.status = new_status
        task.completed_at = (
            timezone.now() if new_status == self.Status.COMPLETED else None
        )
        task.save(update_fields=("status", "completed_at", "updated_at"))
        self.refresh_from_db()
        return task
