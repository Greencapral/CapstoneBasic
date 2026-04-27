from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Список URL‑маршрутов приложения Django. Определяет, какие URL‑адреса
# доступны в проекте и какие представления (views) им соответствуют.
urlpatterns = [
    # Маршрут для административной панели Django.
    # Открывает доступ к интерфейсу администратора по адресу /admin/.
    path("admin/", admin.site.urls),

    # Маршрутизация для приложения управления пользователями.
    # Включает URL‑шаблоны из модуля custom_user_app.urls под префиксом /user/.
    path("user/", include("custom_user_app.urls")),

    # Основная маршрутизация веб‑скрапинга.
    # Включает все URL‑шаблоны из модуля web_scraping.urls без префикса.
    # Это означает, что маршруты из web_scraping.urls будут доступны
    # напрямую в корневом пространстве имён.
    path("", include("web_scraping.urls")),
] + static(
    # Настройка обслуживания статических файлов (CSS, JS, изображения)
    # в режиме разработки.
    #
    # Параметры:
    # - settings.STATIC_URL: базовый URL для доступа к статическим файлам
    #   (определён в настройках проекта, обычно '/static/').
    # - document_root=settings.STATIC_ROOT: физическая директория на сервере,
    #   где хранятся собранные статические файлы.
    settings.STATIC_URL,
    document_root=settings.STATIC_ROOT
)
