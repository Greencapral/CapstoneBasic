import re
import subprocess

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from django.db import transaction
import time
import random

from web_scraping.models import (
    Product,
    Marketplace,
)
from config import is_docker_container

class Parser:
    """
    Класс парсера для работы с маркетплейсами через Selenium WebDriver.
    Инициализирует основные атрибуты парсера, включая настройки браузера,
    состояние драйвера и связь с записью маркетплейса в БД.
    """

    def __init__(self, name_mp, headless):
        """
        Инициализирует экземпляр парсера с заданными параметрами.
        Создаёт базовые атрибуты для хранения состояния парсера (драйвер,
        настройки запуска и т.д.), а также находит соответствующий
        маркетплейс в базе данных по имени.

        Args:
            name_mp (str): Название маркетплейса, который будет использоваться
                для парсинга (искомое значение в поле name модели Marketplace).
            headless (bool, optional): Флаг запуска браузера в headless‑режиме
                (без графического интерфейса). По умолчанию True.

        Attributes:
            headless (bool): Сохраняет значение параметра headless для
                дальнейшего использования при настройке драйвера.
            driver (webdriver or None): Хранит экземпляр WebDriver после его
                инициализации (изначально None).
            marketplace (Marketplace or None): Объект маркетплейса из БД
                (загружается по имени при инициализации).
            search_query (str or None): Текущий поисковый запрос для парсинга
                (изначально None, устанавливается позже).

        Raises:
            Marketplace.DoesNotExist: Если маркетплейс с указанным именем
                не найден в базе данных — исключение не перехватывается,
                должно обрабатываться вызывающим кодом.
        """
        self.headless = headless  # Сохраняем флаг headless‑режима для дальнейшей настройки драйвера
        self.driver = None  # Инициализируем атрибут драйвера как None (будет создан позже)
        self.marketplace = None  # Инициализируем атрибут маркетплейса как None
        self.search_query = None  # Инициализируем атрибут поискового запроса как None

        # Находим маркетплейс в БД по переданному имени
        self.marketplace = Marketplace.objects.get(name=name_mp)
        print(
            f"Marketplace найден: {self.marketplace}, ID: {self.marketplace.id}"
        )  # Выводим информацию о найденном маркетплейсе для подтверждения корректности инициализации

    def setup_driver(self):
        """
        Настраивает и инициализирует WebDriver для Selenium с оптимизированными опциями.
        Устанавливает различные аргументы и экспериментальные опции для обхода
        обнаружения автоматизации, настраивает размер окна и User‑Agent. В зависимости
        от окружения (Docker или локальная машина) создаёт соответствующий драйвер.

        Args:
            self (object): Экземпляр класса парсера, содержащий атрибуты:
                - headless (bool): флаг запуска в headless‑режиме;
                - driver (webdriver): атрибут для хранения инициализированного драйвера.

        Raises:
            Exception: Если произошла ошибка при установке или инициализации драйвера,
                исключение перехватывается, выводится сообщение и повторно поднимается.
        """
        options = Options()
        # if self.headless:
        #     options.add_argument("--headless")  # Запуск браузера без графического интерфейса (headless‑режим)

        # Базовые аргументы для стабильной работы драйвера
        options.add_argument("--no-sandbox")  # Отключение песочницы для повышения стабильности в контейнерах
        options.add_argument("--disable-dev-shm-usage")  # Обход ограничений по памяти в Docker
        if is_docker_container():
            options.binary_location = "/usr/bin/chromium"  # Указываем путь к Chromium
            options.add_argument("--disable-gpu")
        if self.headless:
            options.add_argument("--headless=new")  # Обновлённый headless-режим
        options.add_argument(
            "--disable-blink-features=AutomationControlled")  # Отключение признаков автоматизации в Blink
        options.add_experimental_option(
            "excludeSwitches", ["enable-automation"]  # Исключение переключателя автоматизации
        )
        options.add_argument("--disable-features=TranslateUI")
        options.add_argument("--disable-component-extensions-with-background-pages")
        # Сетевые настройки
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument("--lang=ru-RU")

        # Настройки отображения
        options.add_argument("--window-size=1920,1080")  # Установка размера окна браузера (1920×1080 px)
        user_agent = get_random_user_agent()

        options.add_argument(f"--user-agent={user_agent}")

        try:
            # Установка сервиса ChromeDriver через ChromeDriverManager
            service = Service(ChromeDriverManager().install())

            # Выбор типа драйвера в зависимости от окружения
            if is_docker_container():
                # В Docker используем Remote WebDriver с указанием URL Selenium Hub
                self.driver = webdriver.Remote(
                    command_executor='http://selenium:4444/wd/hub',
                    options=options
                )
            else:
                # Локально используем стандартный Chrome WebDriver
                self.driver = webdriver.Chrome(service=service, options=options)

            # Скрипт для скрытия признака автоматизации: переопределяем свойство navigator.webdriver
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            # Полное удаление признаков автоматизации через CDP
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": """
                        // Удаляем флаг webdriver
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });

                        // Имитируем реальные языки
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['ru-RU', 'ru', 'en-US', 'en']
                        });

                        // Имитируем плагины
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [1, 2, 3, 4, 5]
                        });

                        // Подделываем permissions
                        const originalQuery = window.navigator.permissions.query;
                        window.navigator.permissions.query = (parameters) => (
                            parameters.name === 'notifications' ?
                                Promise.resolve({ state: Notification.permission }) :
                                originalQuery(parameters)
                        );
                    """
                }
            )
            print(user_agent)
        except Exception as e:
            print(f"Ошибка инициализации драйвера: {e}")  # Вывод сообщения об ошибке
            raise  # Повторное поднятие исключения для обработки на более высоком уровне

    @transaction.atomic
    def save_products_to_db(self, products_data):
        """
        Сохраняет данные о товарах в базу данных с обработкой дубликатов и изменений цены.

        Для каждого товара проверяет наличие в БД: если товар существует, обновляет данные
        при изменении цены; если товара нет — создаёт новую запись. Выполняется в рамках
        транзакции для обеспечения целостности данных.

        Args:
            self (object): Экземпляр класса парсера с атрибутами:
                - marketplace (Marketplace): объект маркетплейса (может быть None);
                - search_query (str): поисковый запрос, по которому были найдены товары.
            products_data (list[dict]): Список словарей с данными о товарах. Каждый словарь
                должен содержать ключи: 'product_id', 'name', 'price', а также может
                содержать 'image_url' и 'url'.

        Returns:
            dict: Словарь с результатами операции:
                - 'saved_count' (int): количество сохранённых/обновлённых товаров;
                - 'total_found' (int): общее количество переданных товаров;
                - 'search_query' (str): исходный поисковый запрос;
                - 'product_ids' (list): список ID всех обработанных товаров.
        """
        saved_count = 0
        all_product_ids = []

        if self.marketplace is None:
            print("Ошибка: marketplace не инициализирован. Запускаем setup_driver()")
            self.setup_driver()  # Инициализируем драйвер, если marketplace не задан

        for product_data in products_data:
            try:
                # ПРОВЕРКА: пропускаем товар, если цена <= 0
                if product_data["price"] <= 0:
                    print(
                        f"Пропускаем товар '{product_data['name']}' (ID: {product_data['product_id']}) — цена <= 0"
                    )
                    continue  # Переходим к следующему товару

                all_product_ids.append(product_data["product_id"])  # Добавляем ID товара в общий список для отчёта

                try:
                    # Попытка найти существующий товар по ID и маркетплейсу
                    existing_product = Product.objects.get(
                        product_id=product_data["product_id"],
                        marketplace=self.marketplace,
                    )

                    # Проверяем, изменилась ли цена товара
                    if existing_product.price == product_data["price"]:
                        print(
                            f"Цена не изменилась для товара '{product_data['name']}' (ID: {product_data['product_id']}), пропускаем сохранение"
                        )
                        continue  # Пропускаем обновление, если цена не изменилась
                    else:
                        print(
                            f"Цена изменилась для товара '{product_data['name']}' (ID: {product_data['product_id']}): "
                            f"{existing_product.price} → {product_data['price']}"
                        )
                        # Обновляем все поля товара
                        existing_product.name = product_data["name"]
                        existing_product.image_url = product_data.get("image_url")
                        existing_product.url = product_data.get("url")
                        existing_product.price = product_data["price"]
                        existing_product.save()  # Сохраняем изменения в БД
                        saved_count += 1  # Увеличиваем счётчик сохранённых товаров

                except Product.DoesNotExist:
                    # Товар не найден — создаём новую запись
                    new_product = Product.objects.create(
                        product_id=product_data["product_id"],
                        marketplace=self.marketplace,
                        name=product_data["name"],
                        price=product_data["price"],
                        image_url=product_data.get("image_url"),
                        url=product_data.get("url"),
                    )
                    saved_count += 1  # Увеличиваем счётчик новых товаров
                    print(
                        f"Добавлен новый товар: '{product_data['name']}' (ID: {product_data['product_id']})"
                    )

            except Exception as save_error:
                print(
                    f"Ошибка сохранения товара {product_data.get('name', 'Unknown')}: {save_error}"
                )
                continue  # Продолжаем обработку следующих товаров при ошибке сохранения

            except Exception as e:
                print(f"Ошибка обработки товара: {e}")
                continue  # Продолжаем цикл при любых других ошибках обработки товара

        print(f"Успешно сохранено/обновлено {saved_count} товаров")
        return {
            "saved_count": saved_count,
            "total_found": len(products_data),
            "search_query": self.search_query,
            "product_ids": all_product_ids  # Возвращаем список ID всех обработанных товаров для дальнейшего использования
        }


    def close(self):
        """
        Безопасное закрытие WebDriver.
        Проверяет наличие драйвера и пытается корректно завершить его работу.
        Игнорирует любые ошибки, возникающие при закрытии (например, если драйвер
        уже закрыт или недоступен).
        """
        if self.driver:  # Проверяем, инициализирован ли драйвер
            try:
                self.driver.quit()  # Корректное завершение работы драйвера и закрытие всех окон браузера
            except Exception:  # Перехватываем любые исключения при закрытии драйвера
                pass  # Игнорируем ошибки — главное, чтобы не прерывать выполнение программы


    def scroll_down_for_5_seconds(self):
        """
        Скроллит страницу вниз в течение 5 секунд плавными шагами.
        """
        try:
            # Получаем высоту viewport
            window_size = self.driver.get_window_size()
            viewport_height = window_size["height"]

            # Расчёт целевой позиции скролла: 2–3 высоты экрана за 5 секунд
            target_scroll = viewport_height * random.randint(2, 3)
            current_scroll = 0

            # Время начала скроллинга
            start_time = time.time()

            while time.time() - start_time < 5:  # Продолжаем, пока не прошло 5 секунд
                # Размер шага скролла (100–300 px)
                scroll_step = random.randint(100, 300)
                current_scroll += scroll_step

                # Корректировка последнего шага, чтобы не превысить целевую позицию
                if current_scroll > target_scroll:
                    current_scroll = target_scroll

                # Выполняем скролл через JavaScript
                self.driver.execute_script(f"window.scrollTo(0, {current_scroll});")

                # Пауза между шагами скролла (0.3–0.8 с) для плавного скролла
                time.sleep(random.uniform(0.3, 0.8))

                # Перерасчёт высоты viewport на случай изменения размера окна
                window_size = self.driver.get_window_size()
                viewport_height = window_size["height"]
                target_scroll = viewport_height * random.randint(2, 3)

            # Финальный скролл до конца страницы (на всякий случай)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        except Exception as e:
            print(f"Ошибка при скроллинге: {e}")


def get_chrome_version():
    """Определяет основную версию браузера Chrome/Chromium в системе.
    Функция пытается получить версию Chrome через системные команды для разных ОС:
    - в Windows — через реестр (reg query);
    - в Linux/macOS — через запуск браузера с флагом --version.

    Returns:
        str or None: основная версия Chrome (например, "123") при успешном
            определении, None — если версию не удалось получить или произошла ошибка.

    Raises:
        Exception: перехватывается внутри функции, выводится сообщение об ошибке,
            но не пробрасывается дальше.
    """
    try:
        # Попытка определить версию Chrome в ОС Windows через реестр.
        cmd = 'reg query "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon" /v version'
        result = subprocess.run(cmd, capture_output=True, shell=True, text=True)
        if result.returncode == 0:
            # Извлекаем версию из вывода команды с помощью регулярного выражения.
            # Ожидаемый формат: строка с "version", "REG_SZ" и номером версии.
            version = re.search(r'version\s+REG_SZ\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
            if version:
                # Возвращаем только основной номер версии (первое число до точки).
                return version.group(1).split('.')[0]

        # Попытка определить версию Chrome/Chromium в Linux или macOS.
        # Пробуем несколько возможных команд запуска браузера.
        for cmd in ['google-chrome --version', 'chrome --version', 'chromium-browser --version']:
            result = subprocess.run(cmd, capture_output=True, shell=True, text=True)
            if result.returncode == 0:
                # Ищем номер версии в выводе команды. Учитываем варианты "Chrome" и "Chromium".
                version = re.search(r'Chrome\s+(\d+)|Chromium\s+(\d+)', result.stdout)
                if version:
                    # Возвращаем номер версии из первой или второй группы захвата.
                    return version.group(1) or version.group(2)
    except Exception as e:
        # При любой ошибке выводим сообщение и продолжаем выполнение.
        print(f"Ошибка определения версии Chrome: {e}")
    # Если ни один способ не сработал или произошла ошибка, возвращаем None.
    return None



def get_random_user_agent():
    """Генерирует случайный User‑Agent на основе текущей версии Chrome.
    На текущий момент возвращает один шаблон User‑Agent для Windows с подстановкой
    актуальной версии Chrome. В перспективе можно расширить список шаблонов
    для разных ОС и браузеров.

    Returns:
        str: строка User‑Agent, например:
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
            (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    """
    chrome_version = get_chrome_version()

    # Список шаблонов User‑Agent. На данный момент содержит один актуальный шаблон.
    user_agents = [
        # Шаблон для Windows 10 с подстановкой версии Chrome.
        # Остальные части строки фиксированы и соответствуют стандартному формату.
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36",
    ]
    # Возвращаем случайно выбранный User‑Agent из списка (в текущем случае — единственный).
    return random.choice(user_agents)


