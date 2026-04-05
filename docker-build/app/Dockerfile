FROM python:3.14.3-slim-trixie

# Устанавливаем системные зависимости для Chrome/ChromeDriver
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libappindicator3-1 \
    libasound2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Установка Google Chrome
RUN wget -q -O /tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i /tmp/google-chrome.deb || true \
    && apt-get update \
    && apt-get -f install -y \
    && if [ -f "/tmp/google-chrome.deb" ]; then rm /tmp/google-chrome.deb; fi

# Установка ChromeDriver с проверкой и установкой зависимостей
RUN apt-get update && apt-get install -y curl unzip && rm -rf /var/lib/apt/lists/* \
    && set -eux; \
    CHROMEDRIVER_VERSION=$(curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE); \
    echo "Installing ChromeDriver version $CHROMEDRIVER_VERSION"; \
    wget -q --no-check-certificate https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip; \
    unzip chromedriver_linux64.zip -d /usr/local/bin/; \
    rm chromedriver_linux64.zip; \
    chmod +x /usr/local/bin/chromedriver; \
    # Проверка установки
    if [ -f "/usr/local/bin/chromedriver" ]; then \
        echo "ChromeDriver installed successfully"; \
        chromedriver --version; \
    else \
        echo "ERROR: ChromeDriver not installed!"; \
        exit 1; \
    fi

# Копируем утилиту uv (менеджер зависимостей) из официального образа
COPY --from=ghcr.io/astral-sh/uv:0.10.0 /uv /uvx /bin/

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы конфигурации проекта
COPY pyproject.toml uv.lock ./

# Синхронизируем зависимости проекта с помощью uv
RUN uv sync --locked --no-install-project --no-dev

# Добавляем виртуальное окружение проекта в PATH
ENV PATH="/app/.venv/bin:$PATH"

# Копируем скрипт точки входа
COPY docker-build/app/entrypoint.sh /etc/entrypoint.sh

# Даём скрипту права на выполнение
RUN chmod +x /etc/entrypoint.sh

# Копируем исходный код приложения
COPY . .

# Задаём точку входа для контейнера
ENTRYPOINT ["/etc/entrypoint.sh"]
