"""Local development settings."""

import os

from .base import *  # noqa: F403
from .base import ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS, SIMPLE_JWT

# Not a secret: a placeholder so the project starts without a .env file.
DEVELOPMENT_SECRET_KEY = "freecook-development-only-key-not-for-production"

DEBUG = True

FRONTEND_URL = os.environ.get("FRONTEND_URL") or "http://localhost:5173"

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or DEVELOPMENT_SECRET_KEY

ALLOWED_HOSTS = ALLOWED_HOSTS or ["localhost", "127.0.0.1", "[::1]"]

CORS_ALLOWED_ORIGINS = CORS_ALLOWED_ORIGINS or ["http://localhost:5173"]

SIMPLE_JWT = {
    **SIMPLE_JWT,
    "SIGNING_KEY": SIMPLE_JWT["SIGNING_KEY"] or SECRET_KEY,
}

# Outgoing email. Without SMTP_HOST it goes to a local Mailpit on port
# 1025, which is what the Docker Compose stack runs.
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("SMTP_HOST") or "localhost"
EMAIL_PORT = int(os.environ.get("SMTP_PORT") or 1025)
EMAIL_HOST_USER = os.environ.get("SMTP_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("SMTP_USE_TLS", "false").lower() == "true"
DEFAULT_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL") or "noreply@freecook.local"

# Text messages are printed to the console, never sent to a real phone.
SMS_BACKEND = os.environ.get("SMS_BACKEND") or "core.sms.ConsoleSmsBackend"
