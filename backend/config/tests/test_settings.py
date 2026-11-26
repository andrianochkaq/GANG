import sys
from datetime import timedelta
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
    monkeypatch.setenv("FRONTEND_URL", "https://freecook.example")
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "freecook.example, api.example")
    monkeypatch.delitem(sys.modules, "config.settings.prod", raising=False)

    prod_settings = import_module("config.settings.prod")

    assert prod_settings.DEBUG is False
    assert prod_settings.SECRET_KEY == "production-secret-key"
    assert prod_settings.ALLOWED_HOSTS == ["freecook.example", "api.example"]
    assert prod_settings.SIMPLE_JWT["SIGNING_KEY"] == "production-jwt-key"
    assert prod_settings.FRONTEND_URL == "https://freecook.example"


def test_jwt_sessions_rotate_and_blacklist_refresh_tokens():
    jwt_settings = settings.SIMPLE_JWT

    assert jwt_settings["ACCESS_TOKEN_LIFETIME"] == timedelta(minutes=15)
    assert jwt_settings["REFRESH_TOKEN_LIFETIME"] == timedelta(days=30)
    assert jwt_settings["ROTATE_REFRESH_TOKENS"] is True
    assert jwt_settings["BLACKLIST_AFTER_ROTATION"] is True
    assert "rest_framework_simplejwt.token_blacklist" in settings.INSTALLED_APPS


def test_prod_settings_require_frontend_url(monkeypatch):
    monkeypatch.setenv("DJANGO_SECRET_KEY", "production-secret-key")
    monkeypatch.setenv("JWT_SECRET_KEY", "production-jwt-key")
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "freecook.example")
    monkeypatch.delenv("FRONTEND_URL", raising=False)
    monkeypatch.delitem(sys.modules, "config.settings.prod", raising=False)

    with pytest.raises(ImproperlyConfigured):
        import_module("config.settings.prod")


def test_password_reset_link_lives_one_hour():
    assert settings.PASSWORD_RESET_TIMEOUT == 60 * 60
