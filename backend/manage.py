#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys


def run_command_line() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as error:
        raise ImportError(
            "Couldn't import Django. Install the requirements with "
            "`pip install -r backend/requirements.txt`."
        ) from error
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    run_command_line()
