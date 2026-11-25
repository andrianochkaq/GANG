"""Validators for account fields."""

import re

from django.core.exceptions import ValidationError

# E.164: a plus sign, a non-zero first digit and 15 digits at most.
PHONE_NUMBER_PATTERN = re.compile(r"\+[1-9][0-9]{1,14}")


def validate_phone_number(value):
    if not PHONE_NUMBER_PATTERN.fullmatch(value):
        raise ValidationError(
            "Введіть номер у міжнародному форматі, наприклад +380501234567.",
            code="invalid_phone_number",
        )
