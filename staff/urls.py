from django.urls import path

from . import views

# namespace for app urls so they can be referenced as `app:name`
app_name = "staff"

urlpatterns = [
    path("", views.index, name="staff"),
]
