from django.urls import path

from .views.phone import PhoneCodeRequestView, PhoneLoginView
from .views.telegram import (
    TelegramLoginStartView,
    TelegramLoginStatusView,
    TelegramWebhookView,
)

urlpatterns = [
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
