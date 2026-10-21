from datetime import date

from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import render

from booking.models import Booking
from common.decorators import account_type_required
from staff_task_assignment.queries import assignments_for

PAGE_SIZE = 10
HISTORY_STATUSES = (
    Booking.Status.CONFIRMED,
    Booking.Status.COMPLETED,
    Booking.Status.CANCELLED,
)


def _parse_date(value):
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


@account_type_required("staff")
def index(request):
    assignments = assignments_for(request.user)
    totals = assignments.aggregate(
        total=Count("pk"),
        upcoming=Count("pk", filter=Q(booking__status=Booking.Status.CONFIRMED)),
        completed=Count("pk", filter=Q(booking__status=Booking.Status.COMPLETED)),
        cancelled=Count("pk", filter=Q(booking__status=Booking.Status.CANCELLED)),
    )
    themes = sorted(
        assignments.order_by().values_list("booking__event_type", flat=True).distinct()
    )

    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    theme = request.GET.get("theme", "")
    date_from = _parse_date(request.GET.get("date_from", ""))
    date_to = _parse_date(request.GET.get("date_to", ""))

    if query:
        assignments = assignments.filter(
            Q(booking__reference__icontains=query)
            | Q(booking__event_name__icontains=query)
            | Q(booking__venue_name__icontains=query)
        )
    if status in HISTORY_STATUSES:
        assignments = assignments.filter(booking__status=status)
    else:
        status = ""
    if theme in themes:
        assignments = assignments.filter(booking__event_type=theme)
    else:
        theme = ""
    if date_from:
        assignments = assignments.filter(booking__event_date__gte=date_from)
    if date_to:
        assignments = assignments.filter(booking__event_date__lte=date_to)

    page = Paginator(
        assignments.order_by("-booking__event_date", "-booking__start_time", "-pk"),
        PAGE_SIZE,
    ).get_page(request.GET.get("page"))

    params = request.GET.copy()
    params.pop("page", None)

    return render(
        request,
        "staff_booking_history/staff_booking_history.html",
        {
            "page": page,
            "totals": totals,
            "themes": themes,
            "status_choices": [(s.value, s.label) for s in HISTORY_STATUSES],
            "query": query,
            "status": status,
            "theme": theme,
            "date_from": date_from.isoformat() if date_from else "",
            "date_to": date_to.isoformat() if date_to else "",
            "querystring": params.urlencode(),
            "has_filters": bool(query or status or theme or date_from or date_to),
        },
    )
