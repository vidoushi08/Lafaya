from functools import wraps

from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login
from django.urls import reverse


def account_type_required(account_type):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(
                    request.get_full_path(),
                    login_url=reverse("authentication:login"),
                )

            if (
                request.user.is_superuser
                or request.user.account_type != account_type
            ):
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator
