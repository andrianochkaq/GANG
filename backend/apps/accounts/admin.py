"""Django admin for users: all three kinds can be created here."""

from django import forms
from django.contrib import admin
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError

from .models import User


class UserCreationForm(forms.ModelForm):
    """Creates a user; the password is optional (passwordless logins)."""

    password1 = forms.CharField(
        label="Пароль",
        required=False,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Залиште порожнім для входу без пароля.",
    )
    password2 = forms.CharField(
        label="Підтвердження пароля",
        required=False,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = User
        fields = ("nickname", "name", "gender", "email", "phone", "telegram_id")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 != password2:
            raise ValidationError("Паролі не збігаються.", code="password_mismatch")
        return password2

    def _post_clean(self):
        super()._post_clean()
        password = self.cleaned_data.get("password2")
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except ValidationError as error:
                self.add_error("password2", error)

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password1")
        if password:
            user.set_password(password)
        else:
            user.password = None
        if commit:
            user.save()
        return user


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "nickname",
        "name",
        "email",
        "phone",
        "telegram_id",
        "is_staff",
        "is_active",
    )
    list_filter = (
        "gender",
        "is_staff",
        "is_superuser",
        "is_active",
        "is_email_verified",
    )
    search_fields = ("nickname", "name", "email", "phone")
    ordering = ("nickname",)
    readonly_fields = ("last_login",)
    filter_horizontal = ("groups", "user_permissions")
    fieldsets = (
        (None, {"fields": ("nickname", "name", "gender")}),
        (
            "Способи входу",
            {"fields": ("email", "is_email_verified", "phone", "telegram_id")},
        ),
        ("Налаштування", {"fields": ("theme_color", "is_onboarding_done")}),
        (
            "Доступ",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Дати", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "nickname",
                    "name",
                    "gender",
                    "email",
                    "phone",
                    "telegram_id",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs["form"] = UserCreationForm
        return super().get_form(request, obj, **kwargs)
