import os
import socket
import re

def is_docker_container():
    """Комплексная проверка запуска в Docker"""

    # Метод 1: Проверка файла /.dockerenv
    if os.path.exists('/.dockerenv'):
        return True

    # Метод 2: Анализ cgroup
    try:
        with open('/proc/1/cgroup', 'r') as f:
            if 'docker' in f.read():
                return True
    except (FileNotFoundError, PermissionError):
        pass

    # Метод 3: Проверка переменных окружения
    if 'container' in os.environ and os.environ['container'] == 'docker':
        return True

    # Метод 4: Проверка hostname
    hostname = socket.gethostname()
    if re.match(r'^[a-f0-9]{12}$', hostname):  # Короткие hex-имена
        return True

    return False
