from pathlib import Path
from dotenv import load_dotenv
import os
from config import is_docker_container

# Базовый путь к директории проекта. Строится от расположения текущего файла,
# поднимается на два уровня вверх для получения корневого каталога проекта.
BASE_DIR = Path(__file__).resolve().parent.parent

# Режим отладки. В продакшене должен быть установлен в False.
# ВНИМАНИЕ: включение отладки в продакшене может привести к утечке данных.
DEBUG = True

# Список хостов, разрешённых для обработки запросов.
# Определяет, с каких доменов/IP-адресов приложение примет HTTP‑запросы.
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
]

# Список разрешённых источников для CORS (Cross-Origin Resource Sharing).
# Определяет, какие внешние домены могут делать запросы к API приложения.
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://0.0.0.0:8000",
]

# URL для доступа к статическим файлам (CSS, JS, изображения и т. д.).
STATIC_URL = '/static/'
# Корневая директория для собранных статических файлов при деплое.
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# Дополнительные директории со статическими файлами для разработки.
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Список установленных приложений Django. Включает стандартные модули Django
# и пользовательские приложения проекта.
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "custom_user_app.apps.CustomUserAppConfig",
    "web_scraping.apps.WebScrapingConfig",
    "django_celery_results",
]

# Цепочка middleware — обработчиков запросов и ответов.
# Определяет порядок выполнения фильтров и проверок для каждого HTTP‑запроса.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Указывает Django, где искать главный файл URL‑маршрутизации проекта.
ROOT_URLCONF = "config.urls"

# Настройки шаблонов Django: движки, директории и контекстные процессоры.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Дополнительные директории с шаблонами помимо стандартных.
        "DIRS": [
            "custom_user_app.templates",
            "web_scraping.templates",
        ],
        # Автоматическое обнаружение шаблонов внутри приложений.
        "APP_DIRS": True,
        "OPTIONS": {
            # Контекстные процессоры добавляют переменные в контекст всех шаблонов.
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Точка входа для WSGI‑сервера (например, Gunicorn).
WSGI_APPLICATION = "config.wsgi.application"

print("IS DOCKER:", is_docker_container())
print("ENV BROKER:", os.getenv("CELERY_BROKER_URL"))

# Конфигурация окружения: разные настройки для Docker и локальной разработки.
if is_docker_container():
    # В Docker: берём настройки из переменных окружения.
    SECRET_KEY = os.getenv("SECRET_KEY")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:63/0")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB'),
            'USER': os.getenv('POSTGRES_USER'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
            'HOST': os.getenv('POSTGRES_HOST', 'pg'),
            'PORT': '5432',
        }
    }
else:
    # Локально: загружаем переменные окружения из .env‑файла.
    load_dotenv()
    SECRET_KEY = os.getenv("SECRET_KEY")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6380/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6380/0")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

print("BROKER:", CELERY_BROKER_URL)

# Валидаторы паролей пользователей. В текущей конфигурации отключены.
# Для включения раскомментируйте нужные блоки.
AUTH_PASSWORD_VALIDATORS = [
    # {
    #     "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    # },
    # {
    #     "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    # },
    # {
    #     "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    # },
    # {
    #     "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    # },
]

# Основные настройки локализации и времени.
LANGUAGE_CODE = "en-us"  # Язык интерфейса по умолчанию.
TIME_ZONE = "Europe/Moscow"  # Часовой пояс сервера.
USE_I18N = True  # Включить поддержку интернационализации.
USE_TZ = True  # Использовать временные зоны при работе с датами.

# Пользовательская модель пользователя вместо стандартной Django.
AUTH_USER_MODEL = "custom_user_app.CustomUser"

# Настройки для Selenium WebDriver.
SELENIUM_DRIVER = "chrome"  # Используемый браузер для автоматизации.
# Запуск браузера без графического интерфейса (GUI).
# False — с отображением окна браузера; True — в фоновом режиме.
SELENIUM_HEADLESS = False
