from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    return HttpResponse("Customer Dashboard")


def manage_profile(request):
    return render(request, "customer_dashboard/manage_profile.html")


def booking_history(request):
    return render(request, "customer_dashboard/booking_history.html")
