import pytest
from django.core.exceptions import ImproperlyConfigured

from core.sms import (
    ConsoleSmsBackend,
    LocMemSmsBackend,
    SentSms,
    SmsBackend,
    SmsError,
    get_sms_backend,
    send_sms,
)

PHONE_NUMBER = "+380501234567"


class RecordingSmsBackend(SmsBackend):
    """A stand-in provider, to prove that a setting is enough to swap it."""

    messages = []

    def send_message(self, phone_number, text):
        self.messages.append((phone_number, text))


class FailingSmsBackend(SmsBackend):
    def send_message(self, phone_number, text):
        raise SmsError("The provider is down.")


@pytest.fixture(autouse=True)
def empty_outboxes():
    LocMemSmsBackend.outbox.clear()
    RecordingSmsBackend.messages.clear()


def test_base_backend_must_be_subclassed():
    with pytest.raises(NotImplementedError):
        SmsBackend().send_message(PHONE_NUMBER, "Hello")


def test_console_backend_prints_the_message(capsys):
    ConsoleSmsBackend().send_message(PHONE_NUMBER, "Hello")

    assert capsys.readouterr().out == f"SMS to {PHONE_NUMBER}: Hello\n"


def test_locmem_backend_keeps_messages_in_the_outbox():
    LocMemSmsBackend().send_message(PHONE_NUMBER, "Hello")

    assert LocMemSmsBackend.outbox == [SentSms(PHONE_NUMBER, "Hello")]


def test_send_sms_uses_the_backend_from_settings(settings):
    settings.SMS_BACKEND = "core.sms.LocMemSmsBackend"

    send_sms(PHONE_NUMBER, "Hello")

    assert LocMemSmsBackend.outbox == [SentSms(PHONE_NUMBER, "Hello")]


def test_changing_the_setting_changes_the_provider(settings):
    settings.SMS_BACKEND = "core.tests.test_sms.RecordingSmsBackend"

    send_sms(PHONE_NUMBER, "Hello")

    assert RecordingSmsBackend.messages == [(PHONE_NUMBER, "Hello")]
    assert LocMemSmsBackend.outbox == []


def test_get_sms_backend_returns_an_instance(settings):
    settings.SMS_BACKEND = "core.sms.ConsoleSmsBackend"

    assert isinstance(get_sms_backend(), ConsoleSmsBackend)


def test_provider_errors_reach_the_caller(settings):
    settings.SMS_BACKEND = "core.tests.test_sms.FailingSmsBackend"

    with pytest.raises(SmsError):
        send_sms(PHONE_NUMBER, "Hello")


def test_missing_backend_setting_is_a_configuration_error(settings):
    settings.SMS_BACKEND = ""

    with pytest.raises(ImproperlyConfigured):
        send_sms(PHONE_NUMBER, "Hello")
