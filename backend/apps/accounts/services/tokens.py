"""JWT pairs for signed-in users."""

from rest_framework_simplejwt.tokens import RefreshToken


def issue_token_pair(user):
    """Return a new refresh and access token for the user."""
    refresh_token = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh_token),
        "access": str(refresh_token.access_token),
    }
