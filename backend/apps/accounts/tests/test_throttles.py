import pytest
from django.core.cache import cache
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from apps.accounts.services.codes import MAX_CODE_REQUESTS_PER_HOUR
from apps.accounts.throttles import CodeIpThrottle, CodeTargetThrottle

REQUEST_FACTORY = APIRequestFactory()


@pytest.fixture(autouse=True)
def local_memory_cache(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "code-throttle-tests",
        },
    }
    cache.clear()


def build_request(data, ip_address="203.0.113.5"):
    http_request = REQUEST_FACTORY.post(
        "/api/auth/email-code/",
        data,
        format="json",
        REMOTE_ADDR=ip_address,
    )
    return Request(http_request)


def count_allowed_requests(throttle_class, make_request, attempts):
    allowed_count = 0
    for _ in range(attempts):
        if throttle_class().allow_request(make_request(), view=None):
            allowed_count += 1
    return allowed_count


def test_code_rates_match_the_service_limit():
    assert CodeIpThrottle().num_requests == MAX_CODE_REQUESTS_PER_HOUR
    assert CodeIpThrottle().duration == 3600
    assert CodeTargetThrottle().num_requests == MAX_CODE_REQUESTS_PER_HOUR
    assert CodeTargetThrottle().duration == 3600


def test_ip_throttle_allows_five_requests_per_hour():
    allowed_count = count_allowed_requests(
        CodeIpThrottle,
        lambda: build_request({"email": "anna@example.com"}),
        MAX_CODE_REQUESTS_PER_HOUR + 3,
    )

    assert allowed_count == MAX_CODE_REQUESTS_PER_HOUR


def test_ip_throttle_counts_each_address_separately():
    for _ in range(MAX_CODE_REQUESTS_PER_HOUR):
        CodeIpThrottle().allow_request(build_request({}), view=None)

    other_request = build_request({}, ip_address="203.0.113.6")

    assert CodeIpThrottle().allow_request(other_request, view=None) is True


def test_target_throttle_allows_five_requests_per_hour_from_any_address():
    attempt_count = MAX_CODE_REQUESTS_PER_HOUR + 3
    ip_addresses = iter(f"203.0.113.{index}" for index in range(attempt_count))

    allowed_count = count_allowed_requests(
        CodeTargetThrottle,
        lambda: build_request({"email": "Anna@Example.com"}, next(ip_addresses)),
        attempt_count,
    )

    assert allowed_count == MAX_CODE_REQUESTS_PER_HOUR


def test_target_throttle_counts_each_target_separately():
    for _ in range(MAX_CODE_REQUESTS_PER_HOUR):
        CodeTargetThrottle().allow_request(
            build_request({"phone": "+380501234567"}), view=None
        )

    other_request = build_request({"phone": "+380671234567"})

    assert CodeTargetThrottle().allow_request(other_request, view=None) is True


def test_target_throttle_ignores_requests_without_a_target():
    allowed_count = count_allowed_requests(
        CodeTargetThrottle,
        lambda: build_request({}),
        MAX_CODE_REQUESTS_PER_HOUR + 3,
    )

    assert allowed_count == MAX_CODE_REQUESTS_PER_HOUR + 3


def test_target_throttle_keeps_the_target_out_of_the_cache_key():
    request = build_request({"email": "anna@example.com"})

    cache_key = CodeTargetThrottle().get_cache_key(request, view=None)

    assert "anna" not in cache_key
