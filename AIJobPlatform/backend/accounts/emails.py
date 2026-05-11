from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse


def build_absolute_api_url(request, route_name, token):
    path = reverse(route_name, kwargs={"token": token})
    return request.build_absolute_uri(path)


def send_verification_email(request, user, token):
    verify_url = build_absolute_api_url(request, "accounts:verify-email", token)
    send_mail(
        subject="Verify your AI Job Portal account",
        message=f"Hi {user.first_name or 'there'},\n\nVerify your email here:\n{verify_url}\n\nThis link expires in 24 hours.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_password_reset_email(request, user, token):
    reset_url = build_absolute_api_url(request, "accounts:password-reset-confirm", token)
    send_mail(
        subject="Reset your AI Job Portal password",
        message=f"Hi {user.first_name or 'there'},\n\nReset your password here:\n{reset_url}\n\nThis link expires in 1 hour.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

