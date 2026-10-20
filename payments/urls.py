from django.urls import path

from . import views

# namespace for app urls so they can be referenced as `app:name`
app_name = "payments"

urlpatterns = [
    path("", views.index, name="payments"),
    path("<int:booking_id>/", views.payment_detail, name="payment_detail"),
    path(
        "<int:booking_id>/demo-payment/",
        views.demo_payment,
        name="demo_payment",
    ),
]
