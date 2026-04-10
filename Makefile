.PHONY: test server redis

# Определение ОС — работает в CMD, PowerShell, Git Bash, WSL
SYSTEM := $(shell \
    powershell -Command " \
        if (Test-Path env:OS) { \
            if ($env:OS -eq 'Windows_NT') { \
                'Windows' \
            } else { \
                $(shell uname 2>nul) \
            } \
        } else { \
            'Windows' \
        }" 2>nul || echo Windows)

test:
	@echo Система: $(SYSTEM)

server:
	uv run python manage.py runserver

# Запуск Redis-контейнера
redis:
ifeq ($(SYSTEM),Windows)
	@chcp 65001 >nul
	@echo Проверка статуса Redis-контейнера...
	@docker start redis-server >nul 2>&1 || docker run -d --name redis-server -p 6379:6379 redis
	@echo ✓ Контейнер Redis запущен (или создан)
else
	@echo Запуск Redis для Unix-систем...
	@if docker ps -a --format "{{.Names}}" | grep -q "^redis-server$$"; then \
		if docker inspect -f '{{.State.Running}}' redis-server 2>/dev/null | grep -q "true"; then \
			echo "✓ Контейнер redis-server уже запущен"; \
	else \
			echo "⏸ Контейнер redis-server остановлен, выполняется запуск..."; \
			docker start redis-server; \
	fi; \
	else \
		echo "➕ Контейнер redis-server не найден, выполняется создание..."; \
		docker run -d --name redis-server -p 6379:6379 redis; \
	fi
endif
