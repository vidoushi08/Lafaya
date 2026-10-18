from django.urls import path

from . import views

app_name = "staff_booking_history"

urlpatterns = [
    path("", views.index, name="history"),
]
