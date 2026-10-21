from django.contrib import messages
from django.shortcuts import redirect, render
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from booking.models import Booking
from common.decorators import account_type_required
from .forms import CustomerProfileForm


@account_type_required("customer")
def index(request):
    return render(request, "customer_dashboard/dashboard.html")


@account_type_required("customer")
def manage_profile(request):
    form = CustomerProfileForm(
        request.POST or None,
        instance=request.user,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("customer_dashboard:manage_profile")

    return render(
        request,
        "customer_dashboard/manage_profile.html",
        {"form": form},
    )


@account_type_required("customer")
def booking_history(request):
    customer_bookings = Booking.objects.filter(customer=request.user)
    today = timezone.localdate()
    summaries = {
        "total_bookings": customer_bookings.count(),
        "upcoming_count": customer_bookings.filter(
            event_date__gte=today,
            status__in=(Booking.Status.PENDING, Booking.Status.APPROVED, Booking.Status.CONFIRMED),
        ).count(),
        "completed_count": customer_bookings.filter(
            status=Booking.Status.CONFIRMED, event_date__lt=today
        ).count(),
        "cancelled_count": customer_bookings.filter(status=Booking.Status.REJECTED).count(),
    }

    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "")
    event_type_filter = request.GET.get("event_type", "")
    bookings = customer_bookings.select_related("payment")
    if search_query:
        bookings = bookings.filter(
            Q(reference__icontains=search_query)
            | Q(event_name__icontains=search_query)
            | Q(event_type__icontains=search_query)
            | Q(venue_name__icontains=search_query)
            | Q(package_name__icontains=search_query)
        )
    if event_type_filter:
        bookings = bookings.filter(event_type__iexact=event_type_filter)
    if status_filter == "confirmed":
        bookings = bookings.filter(status=Booking.Status.CONFIRMED, event_date__gte=today)
    elif status_filter == "completed":
        bookings = bookings.filter(status=Booking.Status.CONFIRMED, event_date__lt=today)
    elif status_filter == "cancelled":
        bookings = bookings.filter(status=Booking.Status.REJECTED)
    elif status_filter == "awaiting_payment":
        bookings = bookings.filter(status=Booking.Status.APPROVED)
    elif status_filter == "pending":
        bookings = bookings.filter(status=Booking.Status.PENDING)

    paginator = Paginator(bookings.order_by("-created_at"), 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    for booking in page_obj.object_list:
        if booking.status == Booking.Status.REJECTED:
            booking.customer_status = "Cancelled"
            booking.customer_status_class = "cancelled"
        elif booking.status == Booking.Status.CONFIRMED and booking.event_date < today:
            booking.customer_status = "Completed"
            booking.customer_status_class = "completed"
        elif booking.status == Booking.Status.CONFIRMED:
            booking.customer_status = "Confirmed"
            booking.customer_status_class = "confirmed"
        elif booking.status == Booking.Status.APPROVED:
            booking.customer_status = "Awaiting payment"
            booking.customer_status_class = "pending"
        else:
            booking.customer_status = "Pending approval"
            booking.customer_status_class = "pending"

    filter_params = request.GET.copy()
    filter_params.pop("page", None)
    event_types = (
        customer_bookings.order_by("event_type")
        .values_list("event_type", flat=True)
        .distinct()
    )
    return render(
        request,
        "customer_dashboard/booking_history.html",
        {
            **summaries,
            "bookings": page_obj.object_list,
            "page_obj": page_obj,
            "search_query": search_query,
            "status_filter": status_filter,
            "event_type_filter": event_type_filter,
            "event_types": event_types,
            "filter_query": filter_params.urlencode(),
        },
    )
