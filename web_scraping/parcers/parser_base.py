import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import (
    ActionChains,
)
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
        if self.headless:
            options.add_argument("--headless")  # Запуск браузера без графического интерфейса (headless‑режим)

        # Базовые аргументы для стабильной работы драйвера
        options.add_argument("--no-sandbox")  # Отключение песочницы для повышения стабильности в контейнерах
        options.add_argument("--disable-dev-shm-usage")  # Обход ограничений по памяти в Docker
        options.add_argument(
            "--disable-blink-features=AutomationControlled")  # Отключение признаков автоматизации в Blink
        options.add_experimental_option(
            "excludeSwitches", ["enable-automation"]  # Исключение переключателя автоматизации
        )
        options.add_experimental_option("useAutomationExtension", False)  # Отключение расширения автоматизации

        # Дополнительные аргументы для минимизации детектирования автоматизации
        options.add_argument("--disable-extensions")  # Отключение всех расширений браузера
        options.add_argument("--disable-plugins")  # Отключение плагинов
        options.add_argument("--disable-popup-blocking")  # Отключение блокировки всплывающих окон
        options.add_argument("--profile-directory=Default")  # Использование стандартного профиля браузера
        options.add_argument(
            "--disable-background-timer-throttling")  # Отключение ограничения таймеров в фоновых вкладках
        options.add_argument("--disable-backgrounding-occluded-windows")  # Отключение приостановки фоновых окон
        options.add_argument("--disable-renderer-backgrounding")  # Отключение фоновой приостановки рендерера

        # Настройки отображения
        options.add_argument("--window-size=1920,1080")  # Установка размера окна браузера (1920×1080 px)
        USER_AGENTS = [
            # Desktop
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.224 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.224 Safari/537.36",

            # New ones
            # "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.224 Safari/537.36 Edg/120.0.2210.144",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            # "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36"
        ]
        user_agent = random.choice(USER_AGENTS)
        options.add_argument(f"--user-agent={user_agent}")
        # user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        # options.add_argument(
        #     f"--user-agent={user_agent}")  # Установка пользовательского User‑Agent для имитации реального браузера

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

    def human_like_actions(self, pages_to_scroll=3):
        """
        Имитирует человеческие действия в браузере: движения курсора и скроллинг страницы.
        Args:
            pages_to_scroll (int): количество страниц для скроллинга (по умолчанию 3)
        """
        try:
            # Получаем размеры окна браузера
            window_size = self.driver.get_window_size()
            viewport_width = window_size["width"]
            viewport_height = window_size["height"]

            # Рассчитываем безопасные отступы (35% от размера viewport)
            safe_margin_x = int(viewport_width * 0.35)
            safe_margin_y = int(viewport_height * 0.35)

            # Определяем границы безопасной зоны для движений курсора
            max_x = viewport_width - safe_margin_x
            min_x = safe_margin_x
            max_y = viewport_height - safe_margin_y
            min_y = safe_margin_y

            # Инициализируем цепочку действий Selenium
            actions = ActionChains(self.driver)

            try:
                # Находим элемент body для относительных перемещений курсора
                body = self.driver.find_element(By.TAG_NAME, "body")
            except Exception as e:
                print(f"Не удалось найти элемент body: {e}")
                return

            def safe_move_to(x, y):
                """
                Безопасное перемещение курсора с ограничением в пределах viewport.
                Args:
                    x (int): координата X для перемещения
                    y (int): координата Y для перемещения

                Returns:
                    tuple: фактические координаты перемещения (safe_x, safe_y)
                """
                # Ограничиваем координаты в пределах безопасной зоны
                safe_x = max(min_x, min(x, max_x))
                safe_y = max(min_y, min(y, max_y))

                try:
                    # Перемещаем курсор с задержкой для имитации человеческого поведения
                    actions.move_to_element_with_offset(body, safe_x, safe_y).perform()
                    time.sleep(random.uniform(0.3, 0.8))
                    return safe_x, safe_y
                except Exception:
                    # Альтернативный метод через JavaScript при ошибке
                    self.driver.execute_script(f"window.scrollTo({safe_x}, {safe_y});")
                    time.sleep(random.uniform(0.5, 1.0))
                    return safe_x, safe_y

            # Начальное случайное перемещение курсора в безопасную зону
            current_x, current_y = safe_move_to(
                random.randint(min_x, max_x),
                random.randint(min_y, max_y)
            )

            # Серия случайных микроперемещений (±40px) для имитации «дрожания» курсора
            for _ in range(random.randint(2, 5)):
                offset_x = random.randint(-40, 40)  # Случайное смещение по X (±40px)
                offset_y = random.randint(-40, 40)  # Случайное смещение по Y (±40px)

                new_x = current_x + offset_x
                new_y = current_y + offset_y

                current_x, current_y = safe_move_to(new_x, new_y)

            # Расчёт целевой позиции скролла (в пикселях)
            target_scroll = viewport_height * pages_to_scroll  # Целевая позиция скролла
            current_scroll = 0  # Текущая позиция скролла

            # Постепенный скроллинг с случайными шагами и паузами
            while current_scroll < target_scroll:
                scroll_step = random.randint(100, 300)  # Размер шага скролла (100–300px)
                current_scroll += scroll_step

                # Корректировка последнего шага, чтобы не превысить целевую позицию
                if current_scroll > target_scroll:
                    current_scroll = target_scroll

                self.driver.execute_script(f"window.scrollTo(0, {current_scroll});")
                time.sleep(random.uniform(0.8, 1.0))  # Пауза между шагами скролла

                # Перерасчёт размеров viewport и границ безопасной зоны (на случай изменения окна)
                window_size = self.driver.get_window_size()
                viewport_width = window_size["width"]
                viewport_height = window_size["height"]

                safe_margin_x = int(viewport_width * 0.35)
                safe_margin_y = int(viewport_height * 0.35)

                max_x = viewport_width - safe_margin_x
                min_x = safe_margin_x
                max_y = viewport_height - safe_margin_y
                min_y = safe_margin_y

                # С вероятностью 30% выполняем случайное микроперемещение курсора во время скролла
                if random.random() < 0.3:
                    offset_x = random.randint(-20, 20)  # Маленькое случайное смещение по X
                    offset_y = random.randint(-20, 20)  # Маленькое случайное смещение по Y

                    new_x = current_x + offset_x
                    new_y = current_y + offset_y
                    current_x, current_y = safe_move_to(new_x, new_y)

            # Финальное перемещение курсора в центр экрана
            center_x = viewport_width // 2
            center_y = viewport_height // 2

            print(f"Попытка финального перемещения в центр: ({center_x}, {center_y})")

            current_x, current_y = safe_move_to(center_x, center_y)
            print("Финальное перемещение выполнено")

        except Exception as e:
            print(f"Критическая ошибка имитации действий: {e}")
