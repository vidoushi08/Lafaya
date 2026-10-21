from django.shortcuts import render

from common.decorators import account_type_required


@account_type_required("customer")
def index(request):
    bookings = (
        request.user.bookings.select_related("payment")
        .all()
        .order_by("-created_at")
    )
    return render(request, "booking/booking.html", {"bookings": bookings})
