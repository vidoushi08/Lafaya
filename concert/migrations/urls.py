from django.urls import path
from . import views

urlpatterns = [
    path('', views.concert_home, name='concert_home'),
]