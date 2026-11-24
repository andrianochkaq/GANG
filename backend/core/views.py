import redis
from django.conf import settings
from django.db import DatabaseError, connection
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

STATUS_OK = "ok"
STATUS_ERROR = "error"
REDIS_TIMEOUT_SECONDS = 2


def check_database() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        return False
    return True


def check_redis() -> bool:
    try:
        client = redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=REDIS_TIMEOUT_SECONDS,
            socket_timeout=REDIS_TIMEOUT_SECONDS,
        )
        return bool(client.ping())
    except redis.RedisError:
        return False


HealthStatusSerializer = inline_serializer(
    name="HealthStatus",
    fields={
        "db": serializers.CharField(),
        "redis": serializers.CharField(),
    },
)


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: HealthStatusSerializer, 503: HealthStatusSerializer},
        summary="Report database and Redis status",
    )
    def get(self, request):
        is_database_up = check_database()
        is_redis_up = check_redis()
        body = {
            "db": STATUS_OK if is_database_up else STATUS_ERROR,
            "redis": STATUS_OK if is_redis_up else STATUS_ERROR,
        }
        is_healthy = is_database_up and is_redis_up
        http_status = (
            status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        return Response(body, status=http_status)
