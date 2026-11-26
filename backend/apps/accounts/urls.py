from django.urls import path

from .views.phone import PhoneCodeRequestView, PhoneLoginView

urlpatterns = [
    path("phone-code/", PhoneCodeRequestView.as_view(), name="phone-code"),
    path("phone-login/", PhoneLoginView.as_view(), name="phone-login"),
]
