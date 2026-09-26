from django.urls import path

from . import views

# namespace for app urls so they can be referenced as `app:name`
app_name = "staff_event_details"

urlpatterns = [
    path("<slug:task_id>/", views.detail, name="detail"),
]
