import pytest
from django.core.exceptions import ValidationError

from apps.accounts.validators import normalize_phone_number

E164_NUMBER = "+380501234567"


@pytest.mark.parametrize(
    "written",
    [
        "+380501234567",
        "  +380501234567  ",
        "+38 (050) 123-45-67",
        "+38.050.123.45.67",
        "0501234567",
        "050 123 45 67",
        "380501234567",
        "00380501234567",
    ],
)
def test_ukrainian_number_is_normalized_to_e164(written):
    assert normalize_phone_number(written) == E164_NUMBER


def test_foreign_number_keeps_its_country_code():
    assert normalize_phone_number("+1 415 555 2671") == "+14155552671"
    assert normalize_phone_number("0044 20 7946 0958") == "+442079460958"


@pytest.mark.parametrize(
    "written",
    [
        "",
        "abc",
        "12345",
        "050123456",
        "+0501234567",
        "+38050123456",
        "+3805012345678",
        "+1234567890123456",
        "+38050123456a",
        "٠٥٠١٢٣٤٥٦٧",
    ],
)
def test_invalid_number_is_refused(written):
    with pytest.raises(ValidationError) as error_info:
        normalize_phone_number(written)

    assert error_info.value.code == "invalid_phone_number"
