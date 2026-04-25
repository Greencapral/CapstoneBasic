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
        # options.add_argument("--disable-gpu")
        if self.headless:
            print('!!!', self.headless)
            options.add_argument("--headless=new")  # Обновлённый headless-режим
        options.add_argument(
            "--disable-blink-features=AutomationControlled")  # Отключение признаков автоматизации в Blink
        options.add_experimental_option(
            "excludeSwitches", ["enable-automation"]  # Исключение переключателя автоматизации
        )
        # options.add_experimental_option("useAutomationExtension", False)  # Отключение расширения автоматизации
        # options.add_argument("--disable-blink-features=AutomationControlled")

        # Дополнительные аргументы для минимизации детектирования автоматизации
        # options.add_argument("--disable-extensions")  # Отключение всех расширений браузера
        # options.add_argument("--disable-plugins")  # Отключение плагинов
        # options.add_argument("--disable-popup-blocking")  # Отключение блокировки всплывающих окон
        # options.add_argument("--profile-directory=Default")  # Использование стандартного профиля браузера
        # options.add_argument(
        #     "--disable-background-timer-throttling")  # Отключение ограничения таймеров в фоновых вкладках
        # options.add_argument("--disable-backgrounding-occluded-windows")  # Отключение приостановки фоновых окон
        # options.add_argument("--disable-renderer-backgrounding")  # Отключение фоновой приостановки рендерера
        options.add_argument("--disable-features=TranslateUI")
        options.add_argument("--disable-component-extensions-with-background-pages")
        # Сетевые настройки
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument("--lang=ru-RU")

        # Настройки отображения
        options.add_argument("--window-size=1920,1080")  # Установка размера окна браузера (1920×1080 px)
        # USER_AGENTS = [
            # Windows
            # "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.224 Safari/537.36",
            # "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            # "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.224 Safari/537.36 Edg/120.0.2210.144",
            #
            # # macOS
            # "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            #
            # # Linux
            # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.112 Safari/537.36",
            # # обновлена версия Chrome
            #
            # # Мобильные устройства
            # "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            # "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36",
            #
            # # Новые добавления
            # "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            # # iPad + Safari
            # "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
            # # Windows + IE 11 (для старых сайтов)
            # "Mozilla/5.0 (Android 13; Tablet; SM-X716B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.83 Safari/537.36",
            # # Android-планшет
            # "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0"
            # Linux + Firefox (альтернатива Chrome)
        # ]
        # user_agent = random.choice(USER_AGENTS)
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
                # self.driver = webdriver.Remote(
                #     command_executor='http://localhost:4444/wd/hub',
                #     options=options
                # )
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

    def warm_up_browser(self):
        """«Разминка» браузера перед парсингом Ozon"""
        # Переходим на Google для имитации «поиска»
        self.driver.get("https://www.google.com")
        time.sleep(random.uniform(2, 4))

        # Имитируем ввод запроса в поиске
        try:
            search_box = self.driver.find_element(By.NAME, "q")
            for char in "Ozon":
                search_box.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            time.sleep(1)
        except:
            pass


def get_chrome_version():
    try:
        # Windows
        cmd = 'reg query "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon" /v version'
        result = subprocess.run(cmd, capture_output=True, shell=True, text=True)
        if result.returncode == 0:
            version = re.search(r'version\s+REG_SZ\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
            if version:
                return version.group(1).split('.')[0]

        # Linux/macOS
        for cmd in ['google-chrome --version', 'chrome --version', 'chromium-browser --version']:
            result = subprocess.run(cmd, capture_output=True, shell=True, text=True)
            if result.returncode == 0:
                version = re.search(r'Chrome\s+(\d+)|Chromium\s+(\d+)', result.stdout)
                if version:
                    return version.group(1) or version.group(2)
    except Exception as e:
        print(f"Ошибка определения версии Chrome: {e}")
    return None


def generate_firefox_version():
    """
    Firefox: версии выходят примерно раз в 4 недели.
    Актуальные версии — в диапазоне 115–130 (2023–2024 гг.).
    """
    return random.randint(115, 130)

def generate_ios_version():
    """
    iOS: мажорные версии выходят раз в год.
    Актуальные версии: 16, 17, 18 (бета).
    """
    versions = [16, 17]
    # 20 % шанс получить бета‑версию 18
    if random.random() < 0.2:
        versions.append(18)
    return random.choice(versions)

def generate_android_version():
    """
    Android: мажорные версии выходят раз в год.
    Актуальные версии: 12, 13, 14.
    Приоритет: 14 (50 %), 13 (30 %), 12 (20 %).
    """
    choices = [14, 13, 12]
    weights = [0.5, 0.3, 0.2]
    return random.choices(choices, weights=weights)[0]

def generate_ie_version():
    """
    Internet Explorer: последняя версия — 11.
    IE больше не обновляется, но используется для совместимости.
    Всегда возвращаем 11, с небольшим шансом (5 %) — 9 или 10.
    """
    # 90 % — IE 11, 5 % — IE 10, 5 % — IE 9
    choices = [11, 10, 9]
    weights = [0.9, 0.05, 0.05]
    return random.choices(choices, weights=weights)[0]


def get_random_user_agent():
    chrome_version = get_chrome_version()
    firefox_version = generate_firefox_version()
    ios_version = generate_ios_version()
    android_version = generate_android_version()
    ie_version = generate_ie_version()
    android_tablet_version = generate_android_version()
    user_agents = [
        # Актуальные версии на 2024 год
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36",
        # f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_{random.randint(15,16)}_{random.randint(0,7)}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{random.randint(16,17)}.0 Safari/605.1.15",
        # f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36",
        #
        # f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36",
        # f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{firefox_version}.0) Gecko/20100101 Firefox/{firefox_version}.0",
        # # f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36 Edg/{edge_version}.0.0.0",
        # f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_{random.randint(15, 16)}_{random.randint(0, 7)}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{random.randint(16, 17)}.0 Safari/605.1.15",
        # # f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36",
        # # f"Mozilla/5.0 (iPhone; CPU iPhone OS {ios_version}_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{safari_version}.2 Mobile/15E148 Safari/604.1",
        # f"Mozilla/5.0 (Linux; Android {android_version}; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Mobile Safari/537.36",
        # # f"Mozilla/5.0 (iPad; CPU OS {ios_version}_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{safari_version}.2 Mobile/15E148 Safari/604.1",
        # f"Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:{ie_version}.0) like Gecko",
        # # f"Mozilla/5.0 (Android {android_tablet_version}; Tablet; SM-X716B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36",
        # f"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:{firefox_version}.0) Gecko/20100101 Firefox/{firefox_version}.0",
    ]
    return random.choice(user_agents)


