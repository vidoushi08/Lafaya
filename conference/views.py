from django.shortcuts import render
from django.urls import reverse


def is_customer(user):
    return (
        user.is_authenticated
        and not user.is_superuser
        and user.account_type == user.AccountType.CUSTOMER
    )


def index(request):
    return render(
        request,
        "conference/conference.html",
        {
            "is_customer": is_customer(request.user),
            "login_next": f"{reverse('conference:conference')}#conference-enquiry",
        },
    )
