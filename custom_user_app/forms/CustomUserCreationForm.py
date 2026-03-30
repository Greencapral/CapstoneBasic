from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.validators import (
    UnicodeUsernameValidator,
)


class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        label="Имя пользователя",
        max_length=70,
        validators=[UnicodeUsernameValidator()],
        help_text="Обязательное поле. Максимум 70 символов. Только буквы, цифры и символы @/./+/-/_.",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Введите имя пользователя",
            }
        ),
    )
    email = forms.EmailField(
        label="Электронная почта",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Введите ваш email",
            }
        ),
    )

    class Meta:
        model = get_user_model()
        fields = (
            "username",
            "email",
        )

    def clean_email(self):
        email = self.cleaned_data.get("email").lower()
        user_model = get_user_model()
        if user_model.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "Этот email уже занят"
            )
        return email

    def clean_username(self):
        """Проверяет уникальность username."""
        username = self.cleaned_data.get("username")
        user_model = get_user_model()
        if user_model.objects.filter(
            username=username
        ).exists():
            raise forms.ValidationError(
                "Это имя пользователя уже занято. Пожалуйста, выберите другое."
            )
        return username
