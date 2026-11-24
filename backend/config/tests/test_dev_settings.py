import sys
from importlib import import_module

import pytest

SMTP_VARIABLE_NAMES = [
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USER",
    "SMTP_PASSWORD",
    "SMTP_USE_TLS",
    "SMTP_FROM_EMAIL",
]


def load_dev_settings(monkeypatch):
    monkeypatch.delitem(sys.modules, "config.settings.dev", raising=False)
    return import_module("config.settings.dev")


@pytest.fixture(autouse=True)
def clear_smtp_variables(monkeypatch):
    for name in SMTP_VARIABLE_NAMES:
        monkeypatch.delenv(name, raising=False)


def test_dev_email_defaults_to_local_mailpit(monkeypatch):
    dev_settings = load_dev_settings(monkeypatch)

    assert dev_settings.EMAIL_HOST == "localhost"
    assert dev_settings.EMAIL_PORT == 1025
    assert dev_settings.EMAIL_USE_TLS is False


def test_dev_email_treats_empty_values_as_unset(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "")
    monkeypatch.setenv("SMTP_PORT", "")

    dev_settings = load_dev_settings(monkeypatch)

    assert dev_settings.EMAIL_HOST == "localhost"
    assert dev_settings.EMAIL_PORT == 1025


def test_dev_email_reads_compose_values(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "mailpit")
    monkeypatch.setenv("SMTP_PORT", "1025")
    monkeypatch.setenv("SMTP_USE_TLS", "false")

    dev_settings = load_dev_settings(monkeypatch)

    assert dev_settings.EMAIL_HOST == "mailpit"
    assert dev_settings.EMAIL_PORT == 1025
    assert dev_settings.EMAIL_USE_TLS is False


def test_dev_email_reads_real_smtp_values(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "mailer")
    monkeypatch.setenv("SMTP_PASSWORD", "mailer-password")
    monkeypatch.setenv("SMTP_USE_TLS", "true")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "hello@freecook.example")

    dev_settings = load_dev_settings(monkeypatch)

    assert dev_settings.EMAIL_HOST == "smtp.example.com"
    assert dev_settings.EMAIL_PORT == 587
    assert dev_settings.EMAIL_HOST_USER == "mailer"
    assert dev_settings.EMAIL_HOST_PASSWORD == "mailer-password"
    assert dev_settings.EMAIL_USE_TLS is True
    assert dev_settings.DEFAULT_FROM_EMAIL == "hello@freecook.example"
