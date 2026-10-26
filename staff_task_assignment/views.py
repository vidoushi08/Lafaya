from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from common.decorators import account_type_required

from .models import StaffTask
from .queries import decorate_tasks, task_counts, tasks_for

PAGE_SIZE = 10


@account_type_required("staff")
def index(request):
    tasks = tasks_for(request.user)

    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    priority = request.GET.get("priority", "")

    if query:
        tasks = tasks.filter(
            Q(title__icontains=query)
            | Q(assignment__booking__reference__icontains=query)
            | Q(assignment__booking__event_name__icontains=query)
            | Q(assignment__booking__venue_name__icontains=query)
            | Q(assignment__booking__client_name__icontains=query)
        )
    if status in StaffTask.Status.values:
        tasks = tasks.filter(status=status)
    else:
        status = ""
    if priority in StaffTask.Priority.values:
        tasks = tasks.filter(priority=priority)
    else:
        priority = ""

    page = Paginator(tasks.order_by("due_date", "pk"), PAGE_SIZE).get_page(
        request.GET.get("page")
    )
    page.object_list = decorate_tasks(page.object_list)

    params = request.GET.copy()
    params.pop("page", None)

    return render(
        request,
        "staff_task_assignment/task_assignment.html",
        {
            "page": page,
            "counts": task_counts(request.user),
            "query": query,
            "status": status,
            "priority": priority,
            "status_choices": StaffTask.Status.choices,
            "priority_choices": StaffTask.Priority.choices,
            "querystring": params.urlencode(),
            "has_filters": bool(query or status or priority),
        },
    )


@require_POST
@account_type_required("staff")
def update_task(request, task_id):
    # Looking the task up through the signed-in staff member makes anyone
    # else's task a 404.
    task = get_object_or_404(tasks_for(request.user), pk=task_id)

    try:
        new_status = request.POST.get("status", "")
        if new_status not in StaffTask.Status.values:
            raise ValidationError("Choose a valid task status.")
        task.transition_to(new_status)
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(
            request, f"“{task.title}” is now {task.get_status_display().lower()}."
        )

    next_url = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = reverse("staff_task_assignment:tasks")
    return redirect(next_url)
