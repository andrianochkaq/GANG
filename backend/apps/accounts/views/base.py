"""Base class and helpers of the sign-in views."""

import ipaddress

from rest_framework.permissions import AllowAny
from rest_framework.throttling import BaseThrottle
from rest_framework.views import APIView

from apps.accounts.api_errors import handle_api_exception


class AuthApiView(APIView):
    """A view anyone may call; it answers with the error shape of the API."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get_exception_handler(self):
        return handle_api_exception


def get_client_ip_address(request):
    """Return the caller's IP address, or None when it is not a valid one.

    The value comes from headers a client can fill in, so it is checked
    before it goes into an IP address column.
    """
    ident = BaseThrottle().get_ident(request)
    try:
        return str(ipaddress.ip_address(ident))
    except ValueError:
        return None
