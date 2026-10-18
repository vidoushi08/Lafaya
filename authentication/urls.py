from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views
from .forms import CaseInsensitivePasswordResetForm

# namespace for app urls so they can be referenced as `app:name`
app_name = "authentication"

urlpatterns = [
    path("", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("verify/sent/", views.verification_sent_view, name="verification_sent"),
    path(
        "verify/resend/",
        views.resend_verification_view,
        name="resend_verification",
    ),
    path(
        "verify/resend/sent/",
        views.verification_resend_done_view,
        name="verification_resend_done",
    ),
    path(
        "verify/<uidb64>/<token>/",
        views.verify_email_view,
        name="verify_email",
    ),
    path(
        "staff-invitation/<uidb64>/<token>/",
        views.staff_invitation_view,
        name="staff_invitation",
    ),
    path(
        "staff-invitation/complete/",
        views.staff_invitation_complete_view,
        name="staff_invitation_complete",
    ),
    path("logout/", views.logout_view, name="logout"),
    path(
        "password/change/",
        auth_views.PasswordChangeView.as_view(
            template_name="authentication/password_change.html",
            success_url=reverse_lazy("authentication:password_change_done"),
        ),
        name="password_change",
    ),
    path(
        "password/change/done/",
        views.password_change_done_view,
        name="password_change_done",
    ),
    path(
        "password/reset/",
        auth_views.PasswordResetView.as_view(
            form_class=CaseInsensitivePasswordResetForm,
            template_name="authentication/password_reset.html",
            email_template_name="authentication/password_reset_email.txt",
            html_email_template_name="authentication/password_reset_email.html",
            subject_template_name="authentication/password_reset_subject.txt",
            success_url=reverse_lazy("authentication:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password/reset/sent/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="authentication/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "password/reset/<uidb64>/<token>/",
        views.LafayaPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password/reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="authentication/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
]
