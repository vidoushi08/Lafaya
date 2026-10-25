from django.shortcuts import get_object_or_404, render

from common.decorators import account_type_required
from staff_task_assignment.queries import assignments_for, decorate_tasks


@account_type_required("staff")
def detail(request, assignment_id):
    # Scoping the lookup to the signed-in staff member makes anyone else's
    # assignment a 404 instead of a hidden link.
    assignment = get_object_or_404(assignments_for(request.user), pk=assignment_id)
    booking = assignment.booking
    tasks = decorate_tasks(
        assignment.tasks.select_related("assignment__booking").order_by(
            "due_date", "pk"
        )
    )
    services = [
        name.strip() for name in booking.services_summary.split(",") if name.strip()
    ]

    return render(
        request,
        "staff_event_details/detail.html",
        {
            "assignment": assignment,
            "booking": booking,
            "tasks": tasks,
            "services": services,
        },
    )
