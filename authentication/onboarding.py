import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import User


def _issue_token(user):
    token = secrets.token_urlsafe(32)
    user.onboarding_token_hash = hashlib.sha256(token.encode()).hexdigest()
    user.onboarding_token_created_at = timezone.now()
    user.save(
        update_fields=("onboarding_token_hash", "onboarding_token_created_at")
    )
    return token


def _send_onboarding_email(user, request, route_name, template_name, subject, timeout):
    token = _issue_token(user)
    url = request.build_absolute_uri(
        reverse(
            route_name,
            kwargs={
                "uidb64": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": token,
            },
        )
    )
    message = render_to_string(
        template_name,
        {
            "user": user,
            "url": url,
            "timeout_hours": max(1, timeout // 3600),
        },
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])


def send_customer_verification(user, request):
    _send_onboarding_email(
        user,
        request,
        "authentication:verify_email",
        "authentication/customer_verification_email.txt",
        "Verify your Lafaya account",
        settings.CUSTOMER_EMAIL_VERIFICATION_TIMEOUT,
    )


def send_staff_invitation(user, request):
    _send_onboarding_email(
        user,
        request,
        "authentication:staff_invitation",
        "authentication/staff_invitation_email.txt",
        "Set up your Lafaya staff account",
        settings.STAFF_INVITATION_TIMEOUT,
    )


def onboarding_token_is_valid(user, token, account_type, timeout):
    if (
        user.is_active
        or user.account_type != account_type
        or not user.onboarding_token_hash
        or user.onboarding_token_created_at is None
    ):
        return False
    if account_type == User.AccountType.CUSTOMER and not user.has_usable_password():
        return False
    if account_type == User.AccountType.STAFF and user.has_usable_password():
        return False
    if user.onboarding_token_created_at + timedelta(seconds=timeout) < timezone.now():
        return False
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return hmac.compare_digest(user.onboarding_token_hash, token_hash)


def can_resend_onboarding_email(user):
    if user.onboarding_token_created_at is None:
        return True
    cooldown = settings.ONBOARDING_EMAIL_RESEND_COOLDOWN
    return user.onboarding_token_created_at + timedelta(seconds=cooldown) <= timezone.now()
