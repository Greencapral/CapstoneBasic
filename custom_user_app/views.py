from django.urls import reverse_lazy
from django.views.generic import FormView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from .forms import (
    CustomAuthenticationForm,
    CustomUserCreationForm,
)


class RegisterView(FormView):
    """
    Представление для регистрации нового пользователя.
    Использует форму CustomUserCreationForm для создания аккаунта.
    После успешной регистрации автоматически авторизует пользователя.
    """

    """Шаблон для отображения формы регистрации."""
    template_name = "custom_user_app/register.html"

    """Форма, используемая для регистрации пользователя."""
    form_class = CustomUserCreationForm

    """URL для перенаправления после успешной регистрации (главная страница)."""
    success_url = reverse_lazy("index")

    def form_valid(self, form):
        """
        Обрабатывает валидную форму регистрации.
        Сохраняет нового пользователя в базу данных и автоматически авторизует его.

        Args:
            form (CustomUserCreationForm): Валидная форма регистрации.

        Returns:
            HttpResponse: Ответ перенаправления на success_url.
        """
        user = form.save()  # Сохраняем нового пользователя в БД
        login(self.request, user)  # Автоматически авторизуем пользователя после регистрации
        return super().form_valid(form)  # Выполняем стандартное поведение (перенаправление)



class CustomLoginView(LoginView):
    """
    Кастомное представление для авторизации пользователя.
    Использует кастомную форму аутентификации и автоматически перенаправляет
    уже авторизованных пользователей.
    """

    """Шаблон для отображения формы входа."""
    template_name = "custom_user_app/login.html"

    """Кастомная форма аутентификации с расширенной валидацией и локализованными сообщениями."""
    authentication_form = CustomAuthenticationForm

    """Если пользователь уже авторизован, перенаправляем его (предотвращает повторный вход)."""
    redirect_authenticated_user = True

    def get_success_url(self):
        """
        Определяет URL для перенаправления после успешной авторизации.

        Returns:
            str: URL главной страницы (index).
        """
        return reverse_lazy("index")  # Перенаправление на главную страницу после входа



class CustomLogoutView(LogoutView):
    """
    Кастомное представление для выхода пользователя из системы.
    После выхода автоматически перенаправляет пользователя на главную страницу.
    """

    """URL для перенаправления после выхода из системы (главная страница)."""
    next_page = reverse_lazy("index")
