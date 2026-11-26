"""Validators for account fields."""

import re

from django.core.exceptions import ValidationError

# E.164: a plus sign, a non-zero first digit and 15 digits at most.
PHONE_NUMBER_PATTERN = re.compile(r"\+[1-9][0-9]{1,14}")
# A Ukrainian number is +380 and nine more digits.
UKRAINIAN_PHONE_NUMBER_PATTERN = re.compile(r"\+380[0-9]{9}")

INVALID_PHONE_NUMBER_MESSAGE = (
    "Введіть номер у міжнародному форматі, наприклад +380501234567."
)

_PHONE_SEPARATOR_PATTERN = re.compile(r"[\s\-().]")
_UKRAINIAN_WITH_COUNTRY_CODE_PATTERN = re.compile(r"380[0-9]{9}")
_UKRAINIAN_LOCAL_PATTERN = re.compile(r"0[0-9]{9}")


def validate_phone_number(value):
    if not PHONE_NUMBER_PATTERN.fullmatch(value):
        raise ValidationError(
            INVALID_PHONE_NUMBER_MESSAGE,
            code="invalid_phone_number",
        )


def normalize_phone_number(value):
    """Return the E.164 form of a phone number or raise ``ValidationError``.

    Spaces, dashes, dots and brackets are dropped, ``00`` counts as ``+``,
    and a Ukrainian number without the country code (``0501234567``) gets
    ``+38``. The same person typing the number differently always gets the
    same result, so one number is one account.
    """
    compact = _PHONE_SEPARATOR_PATTERN.sub("", str(value))
    if compact.startswith("00"):
        compact = "+" + compact[2:]
    elif _UKRAINIAN_WITH_COUNTRY_CODE_PATTERN.fullmatch(compact):
        compact = "+" + compact
    elif _UKRAINIAN_LOCAL_PATTERN.fullmatch(compact):
        compact = "+38" + compact
    validate_phone_number(compact)
    is_ukrainian = compact.startswith("+380")
    if is_ukrainian and not UKRAINIAN_PHONE_NUMBER_PATTERN.fullmatch(compact):
        raise ValidationError(
            INVALID_PHONE_NUMBER_MESSAGE,
            code="invalid_phone_number",
        )
    return compact
