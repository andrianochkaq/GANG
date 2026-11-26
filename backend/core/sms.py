"""Pluggable SMS sending.

The backend is a class named by the ``SMS_BACKEND`` setting (a dotted
path), so changing the provider is a settings change and no view needs to
know which provider is in use. A provider adds one ``SmsBackend``
subclass here or anywhere else on the Python path.

- ``ConsoleSmsBackend``: prints the message; the development default.
- ``LocMemSmsBackend``: keeps messages in ``outbox``; used by tests.
"""

import sys
from typing import NamedTuple

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string


class SmsError(Exception):
    """A message could not be handed to the SMS provider."""


class SentSms(NamedTuple):
    phone_number: str
    text: str


class SmsBackend:
    """Base class of every SMS backend."""

    def send_message(self, phone_number, text):
        """Send ``text`` to an E.164 phone number or raise ``SmsError``."""
        raise NotImplementedError("Subclasses of SmsBackend must send messages.")


class ConsoleSmsBackend(SmsBackend):
    """Writes the message to the standard output instead of sending it."""

    def send_message(self, phone_number, text):
        sys.stdout.write(f"SMS to {phone_number}: {text}\n")
        sys.stdout.flush()


class LocMemSmsBackend(SmsBackend):
    """Keeps every message in the class-level ``outbox`` list."""

    outbox = []

    def send_message(self, phone_number, text):
        self.outbox.append(SentSms(phone_number, text))


def get_sms_backend():
    """Return an instance of the backend named by ``settings.SMS_BACKEND``."""
    backend_path = getattr(settings, "SMS_BACKEND", "")
    if not backend_path:
        raise ImproperlyConfigured("Set the SMS_BACKEND environment variable.")
    return import_string(backend_path)()


def send_sms(phone_number, text):
    """Send a message through the configured backend."""
    get_sms_backend().send_message(phone_number, text)
