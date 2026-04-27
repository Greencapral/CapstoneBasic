import os


def is_docker_container():
    """Проверяет, выполняется ли текущий процесс внутри Docker‑контейнера.
    Функция определяет окружение выполнения по значению переменной окружения
    ENVIRONMENT. Если значение равно "docker", считается, что код
    запущен внутри контейнера.

    Returns:
        bool: True, если код выполняется в Docker‑контейнере, иначе False.
    """
    return os.getenv("ENVIRONMENT") == "docker"