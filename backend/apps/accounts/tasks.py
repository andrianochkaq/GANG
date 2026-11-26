"""Celery tasks of the accounts app."""

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from apps.accounts.services.codes import CODE_TTL_MINUTES

EMAIL_CODE_SUBJECT = "Код підтвердження FreeCook"
EMAIL_CODE_MAX_RETRIES = 3


@shared_task(
    autoretry_for=(OSError,),
    retry_backoff=True,
    max_retries=EMAIL_CODE_MAX_RETRIES,
)
def send_email_code(email, code):
    """Email a confirmation code. A mail server that is down is retried."""
    send_mail(
        EMAIL_CODE_SUBJECT,
        _build_code_text(code),
        settings.DEFAULT_FROM_EMAIL,
        [email],
    )


def _build_code_text(code):
    return (
        f"Ваш код підтвердження: {code}\n\n"
        f"Код діє {CODE_TTL_MINUTES} хв. Нікому його не показуйте.\n"
        "Якщо ви не реєструвалися у FreeCook, просто проігноруйте цей лист."
    )


PASSWORD_RESET_SUBJECT = "Відновлення пароля FreeCook"


@shared_task(
    autoretry_for=(OSError,),
    retry_backoff=True,
    max_retries=EMAIL_CODE_MAX_RETRIES,
)
def send_password_reset_email(email, reset_url):
    """Email the link that sets a new password. A down mail server is retried."""
    send_mail(
        PASSWORD_RESET_SUBJECT,
        _build_reset_text(reset_url),
        settings.DEFAULT_FROM_EMAIL,
        [email],
        html_message=render_to_string(
            "emails/password_reset.html",
            {"reset_url": reset_url},
        ),
    )


def _build_reset_text(reset_url):
    return (
        "Ви попросили відновити пароль у FreeCook. "
        "Щоб задати новий, відкрийте посилання:\n\n"
        f"{reset_url}\n\n"
        "Посилання діє одну годину і спрацьовує лише один раз.\n"
        "Якщо це були не ви, просто проігноруйте цей лист: пароль не зміниться."
    )
