"""Celery tasks of the accounts app."""

from celery import shared_task
from django.core.mail import send_mail

from apps.accounts.services.codes import CODE_TTL_MINUTES

EMAIL_CODE_SUBJECT = "Код підтвердження FreeCook"
EMAIL_CODE_BODY = (
    "Ваш код підтвердження: {code}\n"
    "\n"
    "Код діє {ttl_minutes} хв. Нікому його не повідомляйте.\n"
    "\n"
    "Якщо ви не реєструвалися у FreeCook, просто проігноруйте цей лист."
)


# smtplib.SMTPException is an OSError, so a refused or dropped SMTP
# connection is retried with a growing delay.
@shared_task(
    autoretry_for=(OSError,),
    retry_backoff=True,
    max_retries=3,
    ignore_result=True,
)
def send_email_code(email, code):
    """Email a confirmation code.

    The code travels through the broker for a few minutes and is not
    stored anywhere else in plain text. Never log it.
    """
    send_mail(
        subject=EMAIL_CODE_SUBJECT,
        message=EMAIL_CODE_BODY.format(code=code, ttl_minutes=CODE_TTL_MINUTES),
        from_email=None,
        recipient_list=[email],
    )
