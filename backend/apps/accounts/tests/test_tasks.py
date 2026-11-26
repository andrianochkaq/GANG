from apps.accounts.services.codes import CODE_TTL_MINUTES
from apps.accounts.tasks import EMAIL_CODE_SUBJECT, send_email_code

EMAIL_ADDRESS = "anna@example.com"


def test_send_email_code_sends_one_email_with_the_code(mailoutbox, settings):
    send_email_code(EMAIL_ADDRESS, "123456")

    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.to == [EMAIL_ADDRESS]
    assert message.from_email == settings.DEFAULT_FROM_EMAIL
    assert message.subject == EMAIL_CODE_SUBJECT
    assert "123456" in message.body


def test_email_tells_how_long_the_code_is_valid(mailoutbox):
    send_email_code(EMAIL_ADDRESS, "123456")

    assert f"{CODE_TTL_MINUTES} хв" in mailoutbox[0].body


def test_send_email_code_retries_when_the_mail_server_fails():
    assert OSError in send_email_code.autoretry_for
    assert send_email_code.max_retries == 3
