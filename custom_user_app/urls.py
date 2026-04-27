from django.urls import path
from .views import (
    RegisterView,
    CustomLoginView,
    CustomLogoutView,
)

# Список URL‑маршрутов для модуля аутентификации и управления пользователями.
# Определяет, какие URL‑адреса соответствуют представлениям (views)
# регистрации, входа и выхода из системы.
urlpatterns = [
    # Маршрут для регистрации новых пользователей.
    #
    # Связывает URL /register/ с представлением RegisterView.
    # Параметры:
    # - "register/": шаблон URL (доступен по адресу <домен>/register/).
    # - RegisterView.as_view(): класс представления, преобразованный в вызываемый
    #   объект для обработки HTTP‑запросов.
    # - name="register": символьное имя маршрута, которое можно использовать
    #   для генерации URL в шаблонах и коде (например, reverse("register")).
    path("register/", RegisterView.as_view(), name="register"),

    # Маршрут для аутентификации пользователей (вход в систему).
    #
    # Связывает URL /login/ с кастомным представлением CustomLoginView.
    # Позволяет переопределить стандартное поведение Django для входа.
    # Параметры:
    # - "login/": шаблон URL (<домен>/login/).
    # - CustomLoginView.as_view(): кастомное представление для обработки
    #   логина пользователя.
    # - name="login": имя маршрута для генерации ссылок (reverse("login")).
    path("login/", CustomLoginView.as_view(), name="login"),

    # Маршрут для завершения сессии пользователя (выход из системы).
    #
    # Связывает URL /logout/ с представлением CustomLogoutView.
    # Даёт возможность настроить логику выхода (например, перенаправление после logout).
    # Параметры:
    # - "logout/": шаблон URL (<домен>/logout/).
    # - CustomLogoutView.as_view(): представление для обработки выхода.
    # - name="logout": имя маршрута для использования в коде и шаблонах
    #   (reverse("logout")).
    path("logout/", CustomLogoutView.as_view(), name="logout"),
]
