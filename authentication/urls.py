from django.urls import path

from . import views

# namespace for app urls so they can be referenced as `app:name`
app_name = "authentication"

urlpatterns = [
    path("", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
]
