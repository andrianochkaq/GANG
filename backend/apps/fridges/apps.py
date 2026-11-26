from django.apps import AppConfig


class FridgesConfig(AppConfig):
    name = "apps.fridges"

    def ready(self):
        from . import signals  # noqa: F401
