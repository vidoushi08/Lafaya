from django.urls import path
from . import views

app_name = "wedding"

urlpatterns = [
    path("", views.index, name="wedding"),
    path("enquiry/", views.enquiry, name="enquiry"),
]