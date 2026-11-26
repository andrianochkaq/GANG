from django.urls import path

from .views.email import (
    EmailCodeRequestView,
    EmailLoginView,
    EmailRegisterView,
    EmailVerifyView,
)
from .views.phone import PhoneCodeRequestView, PhoneLoginView
from .views.session import LogoutView, SessionRefreshView
from .views.telegram import (
    TelegramLoginStartView,
    TelegramLoginStatusView,
    TelegramWebhookView,
)

urlpatterns = [
    path("email-register/", EmailRegisterView.as_view(), name="email-register"),
    path("email-code/", EmailCodeRequestView.as_view(), name="email-code"),
    path("email-verify/", EmailVerifyView.as_view(), name="email-verify"),
    path("email-login/", EmailLoginView.as_view(), name="email-login"),
    path("refresh/", SessionRefreshView.as_view(), name="refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("phone-code/", PhoneCodeRequestView.as_view(), name="phone-code"),
    path("phone-login/", PhoneLoginView.as_view(), name="phone-login"),
    path(
        "telegram/start/",
        TelegramLoginStartView.as_view(),
        name="telegram-start",
    ),
    path(
        "telegram/status/<str:token>/",
        TelegramLoginStatusView.as_view(),
        name="telegram-status",
    ),
    path(
        "telegram/webhook/",
        TelegramWebhookView.as_view(),
        name="telegram-webhook",
    ),
]
