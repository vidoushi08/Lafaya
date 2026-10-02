from django.shortcuts import render

from common.location import load_cities
from .models import User


def login_view(request):
    return render(request, "authentication/login.html")


def register_view(request):
    return render(
        request,
        "authentication/register.html",
        {
            "cities": load_cities(),
            "gender_choices": User.Gender.choices,
        },
    )
