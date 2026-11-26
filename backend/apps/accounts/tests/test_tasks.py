import re
import smtplib

import pytest
from celery.exceptions import Retry
from django.core import mail

from apps.accounts.services.codes import CODE_TTL_MINUTES
from apps.accounts.tasks import EMAIL_CODE_SUBJECT, send_email_code


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
