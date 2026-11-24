import sys
from importlib import import_module

import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from config.celery import celery_app

PROJECT_APP_NAMES = [
    "accounts",
    "fridges",
    "products",
    "shopping",
    "chef",
    "nutrition",
    "recipes",
    "receipts",
]


@pytest.mark.parametrize("app_name", PROJECT_APP_NAMES)
def test_installed_apps_include_project_app(app_name):
    assert f"apps.{app_name}" in settings.INSTALLED_APPS


def test_database_uses_postgresql():
    engine = settings.DATABASES["default"]["ENGINE"]

    assert engine == "django.db.backends.postgresql"


def test_celery_uses_redis_as_broker():
    assert celery_app.conf.broker_url == settings.REDIS_URL


def test_prod_settings_require_secret_key(monkeypatch):
    monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)
    monkeypatch.delitem(sys.modules, "config.settings.prod", raising=False)

    with pytest.raises(ImproperlyConfigured):
        import_module("config.settings.prod")


def test_prod_settings_read_values_from_environment(monkeypatch):
    monkeypatch.setenv("DJANGO_SECRET_KEY", "production-secret-key")
    monkeypatch.setenv("JWT_SECRET_KEY", "production-jwt-key")
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "freecook.example, api.example")
    monkeypatch.delitem(sys.modules, "config.settings.prod", raising=False)

    prod_settings = import_module("config.settings.prod")

    assert prod_settings.DEBUG is False
    assert prod_settings.SECRET_KEY == "production-secret-key"
    assert prod_settings.ALLOWED_HOSTS == ["freecook.example", "api.example"]
    assert prod_settings.SIMPLE_JWT["SIGNING_KEY"] == "production-jwt-key"
