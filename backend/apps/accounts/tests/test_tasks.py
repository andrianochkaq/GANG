import re
import smtplib

import pytest
from celery.exceptions import Retry
from django.core import mail

from apps.accounts.services.codes import CODE_TTL_MINUTES
from apps.accounts.tasks import (
    EMAIL_CODE_SUBJECT,
    PASSWORD_RESET_SUBJECT,
    send_email_code,
    send_password_reset_email,
)


def test_task_sends_one_letter_with_the_code():
    send_email_code("anna@example.com", "123456")

    assert len(mail.outbox) == 1
    letter = mail.outbox[0]
    assert letter.to == ["anna@example.com"]
    assert letter.subject == EMAIL_CODE_SUBJECT
    assert re.search(r"\b123456\b", letter.body)
    assert f"{CODE_TTL_MINUTES} хв" in letter.body


def test_task_retries_when_the_mail_server_is_down(monkeypatch):
    def fail_to_send(*args, **kwargs):
        raise smtplib.SMTPConnectError(421, "Service not available")

    monkeypatch.setattr("apps.accounts.tasks.send_mail", fail_to_send)

    with pytest.raises(Retry):
        send_email_code.apply(args=("anna@example.com", "123456"), throw=True)


def test_reset_task_sends_one_letter_with_the_link():
    link = "https://app.freecook.example/reset-password?uid=abc&token=def"

    send_password_reset_email("anna@example.com", link)

    assert len(mail.outbox) == 1
    letter = mail.outbox[0]
    assert letter.to == ["anna@example.com"]
    assert letter.subject == PASSWORD_RESET_SUBJECT
    assert link in letter.body
    assert "одну годину" in letter.body
    html, mimetype = letter.alternatives[0]
    assert mimetype == "text/html"
    assert "uid=abc&amp;token=def" in html


def test_reset_task_retries_when_the_mail_server_is_down(monkeypatch):
    def fail_to_send(*args, **kwargs):
        raise smtplib.SMTPConnectError(421, "Service not available")

    monkeypatch.setattr("apps.accounts.tasks.send_mail", fail_to_send)

    with pytest.raises(Retry):
        send_password_reset_email.apply(
            args=("anna@example.com", "https://app.freecook.example/x"),
            throw=True,
        )
