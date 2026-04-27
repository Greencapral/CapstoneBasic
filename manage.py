import os
import sys


def main():
    """Запускает административные задачи Django.
    Устанавливает модуль настроек Django и выполняет команду, переданную через
    командную строку (например, `runserver`, `migrate`, `makemigrations` и т.д.).

    Эта функция — точка входа для утилит управления Django (manage.py).

    Raises:
        ImportError: если Django не установлен или недоступен в текущем окружении.
            В сообщении об ошибке приводятся возможные причины проблемы:
            * Django не установлен;
            * переменная окружения PYTHONPATH не настроена;
            * виртуальное окружение не активировано.
    """
    # Устанавливает переменную окружения DJANGO_SETTINGS_MODULE,
    # которая указывает Django, какой модуль настроек использовать.
    # В данном случае — config.settings (файл settings.py в директории config).
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    try:
        # Импортирует функцию execute_from_command_line из модуля управления Django.
        # Эта функция обрабатывает аргументы командной строки и запускает соответствующую команду Django.
        from django.core.management import (
            execute_from_command_line,
        )
    except ImportError as exc:
        # Обрабатывает ошибку импорта Django.
        # Если Django не найден, выбрасывает исключение с подробным сообщением,
        # помогающим пользователю диагностировать проблему.
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Выполняет команду Django, переданную в командной строке (sys.argv).
    # Например:
    # - `python manage.py runserver` — запуск сервера разработки;
    # - `python manage.py migrate` — применение миграций БД;
    # - `python manage.py makemigrations` — создание новых миграций.
    execute_from_command_line(sys.argv)



# Проверяет, запускается ли скрипт напрямую (а не импортируется как модуль).
# Если условие истинно, вызывает функцию main() — это стандартная практика
# для определения точки входа в Python‑скрипте.
if __name__ == "__main__":
    main()
