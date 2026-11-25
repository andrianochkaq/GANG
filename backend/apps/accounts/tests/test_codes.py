from datetime import UTC, datetime, timedelta

import pytest

from apps.accounts.models import CodePurpose, OneTimeCode
from apps.accounts.services import codes
from apps.accounts.services.codes import (
    CODE_LENGTH,
    CODE_TTL_MINUTES,
    MAX_CODE_ATTEMPTS,
    MAX_CODE_REQUESTS_PER_HOUR,
    RESEND_COOLDOWN_SECONDS,
    CodeAttemptsExceededError,
    CodeExpiredError,
    CodeInvalidError,
    CodeRequestLimitError,
    CodeResendTooSoonError,
    delete_expired_codes,
    issue_code,
    verify_code,
)

pytestmark = pytest.mark.django_db

EMAIL_ADDRESS = "anna@example.com"
PHONE_NUMBER = "+380501234567"
IP_ADDRESS = "203.0.113.5"


class FakeClock:
    def __init__(self):
        self.now = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)

    def advance(self, **time_parts):
        self.now += timedelta(**time_parts)


@pytest.fixture
def clock(monkeypatch):
    fake_clock = FakeClock()
    monkeypatch.setattr(codes, "_get_current_time", lambda: fake_clock.now)
    return fake_clock


def wrong_code_for(code):
    return "000000" if code != "000000" else "111111"


def test_issue_code_returns_a_six_digit_code(clock):
    code = issue_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS)

    assert len(code) == CODE_LENGTH
    assert code.isdigit()


def test_issue_code_stores_one_row_that_expires_in_ten_minutes(clock):
    issue_code(CodePurpose.PHONE_LOGIN, PHONE_NUMBER, ip_address=IP_ADDRESS)

    one_time_code = OneTimeCode.objects.get()
    assert one_time_code.purpose == CodePurpose.PHONE_LOGIN
    assert one_time_code.target == PHONE_NUMBER
    assert one_time_code.ip_address == IP_ADDRESS
    assert one_time_code.attempt_count == 0
    assert one_time_code.is_used is False
    assert one_time_code.expires_at == clock.now + timedelta(minutes=CODE_TTL_MINUTES)


def test_code_is_never_stored_in_plain_text(clock):
    code = issue_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS)

    stored_values = OneTimeCode.objects.values().get().values()
    assert code not in [str(value) for value in stored_values]
    one_time_code = OneTimeCode.objects.get()
    assert len(one_time_code.code_hash) == 64
    assert one_time_code.code_hash == codes._hash_code(
        CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS, code
    )


def test_hash_differs_for_another_target_or_purpose():
    code = "123456"

    email_hash = codes._hash_code("email_verification", EMAIL_ADDRESS, code)

    assert email_hash != codes._hash_code("email_verification", "bob@x.com", code)
    assert email_hash != codes._hash_code("phone_login", EMAIL_ADDRESS, code)


def test_issue_code_refuses_an_unknown_purpose(clock):
    with pytest.raises(ValueError):
        issue_code("password_reset", EMAIL_ADDRESS)


def test_verify_code_accepts_the_right_code_once(clock):
    code = issue_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS)

    verify_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS, code)

    assert OneTimeCode.objects.get().is_used is True
    with pytest.raises(CodeInvalidError):
        verify_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS, code)


def test_verify_code_ignores_case_and_spaces_of_the_target(clock):
    code = issue_code(CodePurpose.EMAIL_VERIFICATION, "  Anna@Example.com ")

    verify_code(CodePurpose.EMAIL_VERIFICATION, "anna@example.com", f" {code} ")

    assert OneTimeCode.objects.get().is_used is True


def test_verify_code_refuses_a_wrong_code_and_counts_the_attempt(clock):
    code = issue_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS)

    with pytest.raises(CodeInvalidError) as error_info:
        verify_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS, wrong_code_for(code))

    assert error_info.value.attempts_left == MAX_CODE_ATTEMPTS - 1
    one_time_code = OneTimeCode.objects.get()
    assert one_time_code.attempt_count == 1
    assert one_time_code.is_used is False


def test_verify_code_refuses_an_unknown_target(clock):
    with pytest.raises(CodeInvalidError):
        verify_code(CodePurpose.PHONE_LOGIN, PHONE_NUMBER, "123456")


def test_verify_code_refuses_a_code_meant_for_another_purpose(clock):
    code = issue_code(CodePurpose.PHONE_LOGIN, PHONE_NUMBER)

    with pytest.raises(CodeInvalidError):
        verify_code(CodePurpose.TELEGRAM_LOGIN, PHONE_NUMBER, code)


def test_verify_code_refuses_after_too_many_attempts(clock):
    code = issue_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS)
    for _ in range(MAX_CODE_ATTEMPTS):
        with pytest.raises(CodeInvalidError):
            verify_code(
                CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS, wrong_code_for(code)
            )

    with pytest.raises(CodeAttemptsExceededError):
        verify_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS, code)

    assert OneTimeCode.objects.get().is_used is False


def test_last_allowed_attempt_still_accepts_the_right_code(clock):
    code = issue_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS)
    for _ in range(MAX_CODE_ATTEMPTS - 1):
        with pytest.raises(CodeInvalidError):
            verify_code(
                CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS, wrong_code_for(code)
            )

    verify_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS, code)

    assert OneTimeCode.objects.get().is_used is True


def test_verify_code_refuses_an_expired_code(clock):
    code = issue_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS)
    clock.advance(minutes=CODE_TTL_MINUTES)

    with pytest.raises(CodeExpiredError):
        verify_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS, code)


def test_verify_code_accepts_a_code_just_before_it_expires(clock):
    code = issue_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS)
    clock.advance(minutes=CODE_TTL_MINUTES, seconds=-1)

    verify_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS, code)


def test_resend_is_refused_during_the_cooldown(clock):
    issue_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS)
    clock.advance(seconds=RESEND_COOLDOWN_SECONDS - 20)

    with pytest.raises(CodeResendTooSoonError) as error_info:
        issue_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS)

    assert error_info.value.retry_after_seconds == 20
    assert OneTimeCode.objects.count() == 1


def test_resend_is_allowed_after_the_cooldown(clock):
    issue_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS)
    clock.advance(seconds=RESEND_COOLDOWN_SECONDS)

    issue_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS)

    assert OneTimeCode.objects.count() == 2


def test_a_new_code_replaces_the_previous_one(clock):
    issue_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS)
    clock.advance(seconds=RESEND_COOLDOWN_SECONDS)
    new_code = issue_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS)

    assert OneTimeCode.objects.filter(is_used=False).count() == 1
    verify_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS, new_code)


def test_cooldown_does_not_block_another_target(clock):
    issue_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS)

    issue_code(CodePurpose.EMAIL_VERIFICATION, "bob@example.com")

    assert OneTimeCode.objects.count() == 2


def request_codes_for_one_target(clock, count):
    for _ in range(count):
        issue_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS)
        clock.advance(seconds=RESEND_COOLDOWN_SECONDS + 1)


def test_target_is_limited_to_five_codes_per_hour(clock):
    request_codes_for_one_target(clock, MAX_CODE_REQUESTS_PER_HOUR)
    seconds_since_first_code = MAX_CODE_REQUESTS_PER_HOUR * (
        RESEND_COOLDOWN_SECONDS + 1
    )

    with pytest.raises(CodeRequestLimitError) as error_info:
        issue_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS)

    assert error_info.value.retry_after_seconds == 3600 - seconds_since_first_code


def test_target_can_ask_again_when_the_hour_has_passed(clock):
    request_codes_for_one_target(clock, MAX_CODE_REQUESTS_PER_HOUR)
    clock.advance(hours=1)

    issue_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS)


def test_ip_address_is_limited_to_five_codes_per_hour(clock):
    for index in range(MAX_CODE_REQUESTS_PER_HOUR):
        issue_code(
            CodePurpose.EMAIL_VERIFICATION,
            f"user{index}@example.com",
            ip_address=IP_ADDRESS,
        )

    with pytest.raises(CodeRequestLimitError):
        issue_code(
            CodePurpose.EMAIL_VERIFICATION,
            "another@example.com",
            ip_address=IP_ADDRESS,
        )
    issue_code(
        CodePurpose.EMAIL_VERIFICATION,
        "another@example.com",
        ip_address="203.0.113.6",
    )


def test_requests_without_an_ip_address_are_not_limited_by_ip(clock):
    for index in range(MAX_CODE_REQUESTS_PER_HOUR + 1):
        issue_code(CodePurpose.EMAIL_VERIFICATION, f"user{index}@example.com")

    assert OneTimeCode.objects.count() == MAX_CODE_REQUESTS_PER_HOUR + 1


def test_delete_expired_codes_keeps_codes_the_limits_still_count(clock):
    issue_code(CodePurpose.EMAIL_VERIFICATION, EMAIL_ADDRESS)
    clock.advance(minutes=30)
    issue_code(CodePurpose.PHONE_LOGIN, PHONE_NUMBER)

    assert delete_expired_codes() == 0

    clock.advance(minutes=31)
    assert delete_expired_codes() == 1
    assert OneTimeCode.objects.get().target == PHONE_NUMBER
