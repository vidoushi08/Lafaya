from django.urls import path

from . import views

# namespace for app urls so they can be referenced as `app:name`
app_name = "staff_task_assignment"

urlpatterns = [
    path("", views.index, name="tasks"),
    path("tasks/<int:task_id>/update/", views.update_task, name="update_task"),
]
