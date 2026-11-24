from unittest.mock import MagicMock, patch

from django.db import OperationalError
from redis.exceptions import ConnectionError as RedisConnectionError

from core.views import check_database, check_redis


def test_health_returns_ok_when_database_and_redis_are_up(client):
    with (
        patch("core.views.check_database", return_value=True),
        patch("core.views.check_redis", return_value=True),
    ):
        response = client.get("/api/health/")

    assert response.status_code == 200
    assert response.json() == {"db": "ok", "redis": "ok"}


def test_health_reports_database_error_when_database_is_down(client):
    with (
        patch("core.views.check_database", return_value=False),
        patch("core.views.check_redis", return_value=True),
    ):
        response = client.get("/api/health/")

    assert response.status_code == 503
    assert response.json() == {"db": "error", "redis": "ok"}


def test_health_reports_redis_error_when_redis_is_down(client):
    with (
        patch("core.views.check_database", return_value=True),
        patch("core.views.check_redis", return_value=False),
    ):
        response = client.get("/api/health/")

    assert response.status_code == 503
    assert response.json() == {"db": "ok", "redis": "error"}


def test_check_database_returns_true_when_query_succeeds():
    with patch("core.views.connection", MagicMock()):
        assert check_database() is True


def test_check_database_returns_false_when_connection_fails():
    broken_connection = MagicMock()
    broken_connection.cursor.side_effect = OperationalError("database is down")
    with patch("core.views.connection", broken_connection):
        assert check_database() is False


def test_check_redis_returns_true_when_ping_succeeds():
    with patch("core.views.redis.from_url") as from_url:
        from_url.return_value.ping.return_value = True
        assert check_redis() is True


def test_check_redis_returns_false_when_connection_fails():
    with patch("core.views.redis.from_url") as from_url:
        from_url.return_value.ping.side_effect = RedisConnectionError("down")
        assert check_redis() is False


def test_docs_page_opens(client):
    response = client.get("/api/docs/")

    assert response.status_code == 200


def test_schema_describes_health_endpoint(client):
    response = client.get("/api/schema/")

    assert response.status_code == 200
    assert b"/api/health/" in response.content
