"""Validators for catalog fields."""

from django.core.exceptions import ValidationError

MAX_ALIAS_LENGTH = 120


def validate_aliases(value):
    """Check that aliases are a list of non-blank strings of sane length."""
    if not isinstance(value, list):
        raise ValidationError(
            "Псевдоніми мають бути списком рядків.",
            code="invalid_aliases",
        )
    for alias in value:
        if not isinstance(alias, str) or not alias.strip():
            raise ValidationError(
                "Кожен псевдонім має бути непорожнім рядком.",
                code="invalid_alias",
            )
        if len(alias) > MAX_ALIAS_LENGTH:
            raise ValidationError(
                f"Псевдонім довший за {MAX_ALIAS_LENGTH} символів.",
                code="alias_too_long",
            )
