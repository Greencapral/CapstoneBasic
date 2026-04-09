from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.validators import (
    UnicodeUsernameValidator,
)


class CustomUserCreationForm(UserCreationForm):
    """
    Кастомная форма создания пользователя.
    Расширяет стандартную форму UserCreationForm, добавляя:
    - поле email как обязательное;
    - валидацию уникальности email и username;
    - локализованные подсказки и сообщения об ошибках;
    - стили Bootstrap через атрибуты CSS‑классов.
    """

    class Meta:
        """
        Метаданные формы.
        Определяют модель и набор полей, используемых в форме.
        """
        model = get_user_model()  # Используем кастомную модель пользователя, если она определена, иначе — стандартную
        fields = (
            "username",  # Поле имени пользователя
            "email",  # Поле электронной почты
        )

    """Поле для ввода имени пользователя с валидацией формата и ограничений по длине."""
    username = forms.CharField(
        label="Имя пользователя",
        max_length=70,
        validators=[UnicodeUsernameValidator()],  # Валидатор для проверки формата имени пользователя
        help_text="Обязательное поле. Максимум 70 символов. Только буквы, цифры и символы @/./+/-/_.",  # Подсказка для пользователя
        widget=forms.TextInput(
            attrs={
                "class": "form-control",  # CSS‑класс для стилизации (Bootstrap)
                "placeholder": "Введите имя пользователя",  # Текст‑подсказка внутри поля ввода
            }
        ),
    )

    """Поле для ввода электронной почты с настройкой отображения."""
    email = forms.EmailField(
        label="Электронная почта",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",  # CSS‑класс для стилизации (Bootstrap)
                "placeholder": "Введите ваш email",  # Текст‑подсказка внутри поля ввода
            }
        ),
    )

    def clean_username(self):
        """
        Валидирует поле username: проверяет уникальность.
        Проверяет, существует ли пользователь с таким именем в базе данных.
        Если имя занято, выбрасывается ошибка валидации.

        Returns:
            str:Очищенное имя пользователя.

        Raises:
            forms.ValidationError: Если имя пользователя уже занято.
        """
        username = self.cleaned_data.get("username")
        user_model = get_user_model()
        if user_model.objects.filter(username=username).exists():
            raise forms.ValidationError(
                "Это имя пользователя уже занято. Пожалуйста, выберите другое."  # Ошибка, если имя уже используется
            )
        return username

    def clean_email(self):
        """
        Валидирует поле email: проверяет уникальность и приводит к нижнему регистру.
        Email приводится к нижнему регистру для унификации хранения и поиска.
        Если email уже существует в базе данных, выбрасывается ошибка валидации.

        Returns:
            str: Очищенный email в нижнем регистре.

        Raises:
            forms.ValidationError: Если email уже занят.
        """
        email = self.cleaned_data.get("email").lower()  # Приводим email к нижнему регистру
        user_model = get_user_model()
        if user_model.objects.filter(email=email).exists():
            raise forms.ValidationError("Этот email уже занят")  # Ошибка, если email уже используется
        return email
