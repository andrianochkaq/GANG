"""Celery tasks of the accounts app."""

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

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
