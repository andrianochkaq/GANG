"""Settings shared by every environment.

Everything that differs between environments is read from environment
variables. The variable names are listed in ``.env.example``.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def require_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise ImproperlyConfigured(f"Set the {name} environment variable.")
    return value


def read_env_list(name: str, default: list[str]) -> list[str]:
    raw_value = os.environ.get(name, "")
    items = [item.strip() for item in raw_value.split(",") if item.strip()]
    return items or default


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")

DEBUG = False

ALLOWED_HOSTS = read_env_list("DJANGO_ALLOWED_HOSTS", [])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    # FreeCook apps
    "apps.accounts",
    "apps.fridges",
    "apps.products",
    "apps.shopping",
    "apps.chef",
    "apps.nutrition",
    "apps.recipes",
    "apps.receipts",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "freecook"),
        "USER": os.environ.get("POSTGRES_USER", "freecook"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation."
        "UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "uk"
TIME_ZONE = "Europe/Kyiv"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Counters live in Redis (the default cache). The code rates must match
    # MAX_CODE_REQUESTS_PER_HOUR in apps/accounts/services/codes.py.
    "DEFAULT_THROTTLE_RATES": {
        "code_ip": "5/hour",
        "code_target": "5/hour",
    },
}

SIMPLE_JWT = {
    "SIGNING_KEY": os.environ.get("JWT_SECRET_KEY", ""),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "FreeCook API",
    "DESCRIPTION": "API of FreeCook: shared fridges, AI Chef and more.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

CORS_ALLOWED_ORIGINS = read_env_list("CORS_ALLOWED_ORIGINS", [])

# Dotted path of the SMS backend class (core/sms.py). Empty means no SMS can
# be sent; the provider for production is chosen in FC-109.
SMS_BACKEND = os.environ.get("SMS_BACKEND", "")

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TIMEZONE = TIME_ZONE
