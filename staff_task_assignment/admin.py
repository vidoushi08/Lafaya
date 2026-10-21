from django.contrib import admin, messages

from authentication.admin_site import superadmin_site
from booking.models import Booking

from .models import StaffAssignment, StaffTask

def warn_about_conflicts(modeladmin, request, assignment):
    for other in assignment.conflicting_assignments():
        modeladmin.message_user(
            request,
            f"{assignment.staff} is also assigned to {other.booking.reference} "
            f"on {other.booking.event_date:%d %b %Y}, "
            f"{other.booking.start_time:%H:%M}-{other.booking.end_time:%H:%M}, "
            "which overlaps this event.",
            level=messages.WARNING,
        )


class StaffTaskInline(admin.TabularInline):
    model = StaffTask
    extra = 1
    fields = ("title", "description", "priority", "due_date", "status", "completed_at")
    readonly_fields = ("status", "completed_at")

    def _booking_is_open(self, obj):
        return obj is None or obj.booking.status == Booking.Status.CONFIRMED

    def has_add_permission(self, request, obj=None):
        return self._booking_is_open(obj)

    def has_change_permission(self, request, obj=None):
        return self._booking_is_open(obj)

    def has_delete_permission(self, request, obj=None):
        return self._booking_is_open(obj)


class StaffAssignmentInline(admin.TabularInline):
    """Lets the admin assign staff from the booking page."""

    model = StaffAssignment
    extra = 0
    fields = ("staff", "role")
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return obj is not None and obj.status == Booking.Status.CONFIRMED

    def has_change_permission(self, request, obj=None):
        return obj is not None and obj.status == Booking.Status.CONFIRMED

    def has_delete_permission(self, request, obj=None):
        return obj is not None and obj.status == Booking.Status.CONFIRMED


@admin.register(StaffAssignment, site=superadmin_site)
class StaffAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "booking",
        "staff",
        "role",
        "event_date",
        "booking_status",
        "open_tasks",
    )
    list_filter = ("booking__status", "booking__event_type", "booking__event_date")
    search_fields = (
        "booking__reference",
        "booking__event_name",
        "staff__username",
        "staff__email",
        "staff__first_name",
        "staff__last_name",
        "role",
    )
    list_select_related = ("booking", "staff")
    inlines = (StaffTaskInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("tasks")

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return ("booking", "staff", "created_by", "created_at")
        return ()

    def get_fields(self, request, obj=None):
        if obj is not None:
            return ("booking", "staff", "role", "created_by", "created_at")
        return ("booking", "staff", "role")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "booking":
            kwargs["queryset"] = Booking.objects.filter(
                status=Booking.Status.CONFIRMED
            ).order_by("event_date", "start_time")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_delete_permission(self, request, obj=None):
        return obj is None or obj.booking.status == Booking.Status.CONFIRMED

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
        warn_about_conflicts(self, request, obj)

    @admin.display(description="Event date", ordering="booking__event_date")
    def event_date(self, assignment):
        return assignment.booking.event_date

    @admin.display(description="Booking status", ordering="booking__status")
    def booking_status(self, assignment):
        return assignment.booking.get_status_display()

    @admin.display(description="Open tasks")
    def open_tasks(self, assignment):
        return sum(
            1
            for task in assignment.tasks.all()
            if task.status != StaffTask.Status.COMPLETED
        )
