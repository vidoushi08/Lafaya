from django.shortcuts import render

from common.decorators import account_type_required


@account_type_required("staff")
def index(request):
    return render(request, "staff_booking_history/staff_booking_history.html")
