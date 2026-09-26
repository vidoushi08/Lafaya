from django.shortcuts import render


def index(request):
    return render(request, "staff_booking_history/staff_booking_history.html")
