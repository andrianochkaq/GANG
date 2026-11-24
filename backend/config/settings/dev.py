"""Local development settings."""
import os

from .base import *  # noqa: F403
from .base import ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS, SIMPLE_JWT, read_env_list

# Not a secret: a placeholder so the project starts without a .env file.
DEVELOPMENT_SECRET_KEY = "freecook-development-only-key-not-for-production"

DEBUG = True

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or DEVELOPMENT_SECRET_KEY

ALLOWED_HOSTS = ALLOWED_HOSTS or ["localhost", "127.0.0.1", "[::1]"]

CORS_ALLOWED_ORIGINS = CORS_ALLOWED_ORIGINS or ["http://localhost:5173"]

SIMPLE_JWT = {
    **SIMPLE_JWT,
    "SIGNING_KEY": SIMPLE_JWT["SIGNING_KEY"] or SECRET_KEY,
}
