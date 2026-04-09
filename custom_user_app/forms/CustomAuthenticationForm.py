from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm



class CustomAuthenticationForm(AuthenticationForm):
    """
    Кастомная форма аутентификации пользователя.

    Расширяет стандартную форму AuthenticationForm, добавляя:
    - кастомные атрибуты для полей в HTML;
    - локализованные сообщения об ошибках;
    - валидацию активности аккаунта.
    """

    """Поле для ввода имени пользователя с настройками отображения и валидации."""
    username = forms.CharField(
        label="Имя пользователя",
        max_length=70,
        widget=forms.TextInput(
            attrs={
                "autofocus": True,  # Поле автоматически получает фокус при загрузке страницы
                "class": "form-control",  # CSS‑класс для стилизации (Bootstrap)
                "placeholder": "Введите ваше имя пользователя",  # Подсказка внутри поля ввода
            }
        ),
    )

    """Поле для ввода пароля с настройками отображения."""
    password = forms.CharField(
        label="Пароль",
        strip=False,  # Не удалять пробелы в начале и конце строки
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",  # CSS‑класс для стилизации (Bootstrap)
                "placeholder": "Введите ваш пароль",  # Подсказка внутри поля ввода (скрытая)
            }
        ),
    )

    """Словарь пользовательских сообщений об ошибках аутентификации."""
    error_messages = {
        "invalid_login": (
            "Пожалуйста, введите правильное имя пользователя и пароль. "
            "Обратите внимание: оба поля могут быть чувствительны к регистру."
        ),  # Сообщение при неверных учётных данных
        "inactive": "Этот аккаунт неактивен.",  # Сообщение для неактивных пользователей
    }

    def clean(self):
        """
        Выполняет валидацию данных формы и аутентификацию пользователя.

        Проверяет наличие имени пользователя и пароля, пытается аутентифицировать
        пользователя, а также проверяет, разрешён ли вход для данного аккаунта.

        Returns:
            dict: Очищенные данные формы (cleaned_data).

        Raises:
            forms.ValidationError: Если аутентификация не удалась или аккаунт неактивен.
        """
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username and password:
            # Попытка аутентификации пользователя
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password,
            )
            if self.user_cache is None:
                # Если аутентификация не прошла, выбрасываем ошибку
                raise forms.ValidationError(
                    self.error_messages["invalid_login"],
                    code="invalid_login",
                    params={"username": self.username_field.verbose_name},
                )
            else:
                # Проверяем, разрешён ли вход для этого пользователя
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def confirm_login_allowed(self, user):
        """
        Проверяет, разрешён ли вход в систему для указанного пользователя.

        Args:
            user (User): Экземпляр пользователя, для которого проверяется доступ.

        Raises:
            forms.ValidationError: Если пользователь неактивен (is_active == False).
        """
        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages["inactive"],
                code="inactive",
            )
