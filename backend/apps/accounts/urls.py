from django.urls import path

from apps.accounts.views.email import (
    EmailLoginView,
    EmailRegisterView,
    EmailResendCodeView,
    EmailVerifyView,
)

urlpatterns = [
    path(
        "email/register/",
        EmailRegisterView.as_view(),
        name="email-register",
    ),
    path(
        "email/verify/",
        EmailVerifyView.as_view(),
        name="email-verify",
    ),
    path(
        "email/resend-code/",
        EmailResendCodeView.as_view(),
        name="email-resend-code",
    ),
    path(
        "email/login/",
        EmailLoginView.as_view(),
        name="email-login",
    ),
]
