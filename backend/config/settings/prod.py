"""Production settings. Every secret must come from the environment."""

from .base import *  # noqa: F403
from .base import SIMPLE_JWT, read_env_list, require_env

DEBUG = False

SECRET_KEY = require_env("DJANGO_SECRET_KEY")

FRONTEND_URL = require_env("FRONTEND_URL")

ALLOWED_HOSTS = read_env_list("DJANGO_ALLOWED_HOSTS", [])
if not ALLOWED_HOSTS:
    require_env("DJANGO_ALLOWED_HOSTS")

SIMPLE_JWT = {
    **SIMPLE_JWT,
    "SIGNING_KEY": require_env("JWT_SECRET_KEY"),
}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
