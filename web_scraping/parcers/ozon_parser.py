import random

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import (
    expected_conditions as EC,
)
from selenium.webdriver.common.action_chains import (
    ActionChains,
)
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from django.db import transaction
from decimal import Decimal, InvalidOperation
import time
import re

from web_scraping.models import (
    Product,
    Marketplace,
)


class OzonParser:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.sb = None
        self.marketplace = None

    def setup_driver(self):
        """Настройка драйвера браузера с улучшенной обработкой ошибок"""
        options = Options()
        if self.headless:
            options.add_argument("--headless")

        # Базовые опции для обхода защиты
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option(
            "excludeSwitches", ["enable-automation"]
        )
        options.add_experimental_option("useAutomationExtension", False)

        # Дополнительные опции для маскировки
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")

        # Разрешение экрана и User-Agent
        options.add_argument("--window-size=1920,1080")
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        options.add_argument(f"--user-agent={user_agent}")

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)

            # Удаление признака автоматизации
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            self.marketplace = Marketplace.objects.get(name="ozon.ru")
            print(
                f"Marketplace найден: {self.marketplace}, ID: {self.marketplace.id}"
            )
        except Exception as e:
            print(f"Ошибка инициализации драйвера: {e}")
            raise

    def search_products(self, search_query, max_pages=3):
        """Поиск товаров с улучшенной обработкой ошибок"""
        if not self.driver:
            self.setup_driver()

        products_data = []
        try:
            search_url = f"https://www.ozon.ru/search/?text={search_query}"
            print(f"Открываем URL: {search_url}")

            self.human_like_actions()
            self.driver.get(search_url)

            # Ждём загрузки страницы
            WebDriverWait(self.driver, 50).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print("Страница загружена успешно")

            for page in range(max_pages):
                print(f"Парсинг страницы {page + 1}...")

                WebDriverWait(self.driver, 50).until(
                    lambda driver: len(
                        driver.find_elements(
                            By.CSS_SELECTOR,
                            "div.tile-root",
                        )
                    )
                    > 0
                )
                print("Карточки товаров загружены")

                page_products = self._parse_current_page()
                products_data.extend(page_products)
                print(f"Найдено товаров на странице: {len(page_products)}")

        except WebDriverException as e:
            print(f"Ошибка WebDriver: {e}")
        except TimeoutException as e:
            print(f"Таймаут ожидания: {e}")
        except Exception as e:
            print(f"Критическая ошибка при парсинге: {e}")
        finally:
            self.close()

        return products_data

    def _parse_current_page(self):
        """Парсинг товаров с актуальными селекторами для Wildberries"""
        products = []
        try:
            # Упрощённый селектор для карточек товаров
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "div.tile-root")
                )
            )
            WebDriverWait(self.driver, 30).until(
                lambda driver: len(
                    driver.find_elements(By.CSS_SELECTOR, "div.tile-root")
                )
                > 0
            )

            product_cards = self.driver.find_elements(
                By.CSS_SELECTOR, "div.tile-root"
            )
            print(f"Найдено карточек: {len(product_cards)}")
            # ДОБАВЛЕННЫЙ КОД: ожидание загрузки ВСЕХ цен на странице
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.visibility_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            "div.ji9_24 div.c35_3_13-a0 .tsHeadline500Medium",
                        )
                    )
                )
                print("Все элементы с ценами загружены")
            except TimeoutException:
                print(
                    "Таймаут ожидания загрузки цен — продолжаем парсинг с доступными данными"
                )

            for card in product_cards:
                # print(card.text)
                try:
                    # Инициализируем product_id заранее
                    product_id = "unknown"

                    # # Название товара
                    try:
                        name_elem = card.find_element(
                            By.CSS_SELECTOR,
                            # "span.tsBody500Medium",
                            "span.tsBody500Medium",
                        )
                        full_text = name_elem.text.strip()

                        # Очищаем от разделителя «/» и лишних пробелов
                        cleaned_name = full_text.replace("/", "").strip()
                        name = cleaned_name
                        print(name)
                    except NoSuchElementException:
                        print(
                            "Не найдено название товара, пропускаем карточку"
                        )
                        continue  # пропускаем товар без названия

                    # Цена
                    try:
                        price_elem = card.find_element(
                            By.CSS_SELECTOR,
                            "span.c35_3_13-a1.tsHeadline500Medium",
                        )
                        price_text = price_elem.text.strip()  # «8 903 ₽»
                        if not price_text:
                            raise NoSuchElementException(
                                "Цена не найдена ни по одному селектору"
                            )

                        # Очищаем текст цены
                        # Удаляем все нецифровые символы, кроме запятой/точки
                        clean_price = re.sub(r"[^\d,.]", "", price_text)
                        # Заменяем запятую на точку для Decimal
                        clean_price = clean_price.replace(",", ".")

                        # Преобразуем в Decimal
                        price = Decimal(clean_price)
                        print(f"Цена: {price}")
                    except (
                        ValueError,
                        InvalidOperation,
                        NoSuchElementException,
                    ) as e:
                        print(f"Ошибка при парсинге цены: {e}")
                        price = Decimal("0.00")

                    # URL товара и извлечение ID
                    try:
                        link_elem = card.find_element(
                            By.CSS_SELECTOR,
                            "a.tile-clickable-element",
                        )
                        product_url = link_elem.get_attribute("href")

                        # Извлекаем ID из URL
                        if product_url:
                            product_id_match = re.search(
                                r"(\d+)(?=\?at=)",
                                product_url,
                            )
                            if product_id_match:
                                product_id = product_id_match.group(1)
                            else:
                                # Альтернативный ID: хеш от URL (ограничиваем до 8 цифр)
                                hash_part = str(
                                    abs(hash(product_url)) % (10**5)
                                ).zfill(5)
                                product_id = "999" + hash_part
                                print(
                                    f"ID не найден в URL: {product_url}, сгенерирован ID: {product_id}"
                                )
                        else:
                            product_url = ""

                    except NoSuchElementException:
                        product_url = ""

                    # Изображение
                    try:
                        image_elem = card.find_element(
                            By.CSS_SELECTOR,
                            "img.b95_3_4-a",
                        )
                        image_url = image_elem.get_attribute("src")
                    except NoSuchElementException:
                        image_url = None

                    print(
                        f"Добавляем товар: ID={product_id}, название={name}, цена={price}"
                    )
                    products.append(
                        {
                            "name": name,
                            "price": price,
                            "product_id": product_id,
                            "image_url": image_url,
                            "url": product_url,
                        }
                    )
                except Exception as card_error:
                    print(f"Ошибка при парсинге карточки: {card_error}")
                    continue
        except Exception as e:
            print(f"Общая ошибка парсинга страницы: {e}")

        return products

    @transaction.atomic
    def save_products_to_db(self, products_data):
        """Сохранение данных в базу с обработкой дубликатов"""
        saved_count = 0

        # Проверка, что marketplace корректно инициализирован
        if self.marketplace is None:
            print(
                "Ошибка: marketplace не инициализирован. Запускаем setup_driver()"
            )
            self.setup_driver()

        for product_data in products_data:
            try:
                product, created = Product.objects.update_or_create(
                    product_id=product_data["product_id"],
                    marketplace=self.marketplace,
                    defaults={
                        "name": product_data["name"],
                        "price": product_data["price"],
                        "image_url": product_data.get("image_url"),
                        "url": product_data.get("url"),
                    },
                )
                if created:
                    saved_count += 1
            except Exception as save_error:
                print(
                    f"Ошибка сохранения товара {product_data.get('name', 'Unknown')}: {save_error}"
                )
                continue
        print(f"Успешно сохранено {saved_count} новых товаров")
        return saved_count

    def close(self):
        """Безопасное закрытие драйвера"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def human_like_actions(self):
        """Имитация человеческого поведения с безопасной обработкой координат"""
        actions = ActionChains(self.driver)

        try:
            # Получаем размер окна с проверкой
            window_size = self.driver.get_window_size()
            max_x = max(100, window_size["width"] - 50)
            max_y = max(100, window_size["height"] - 50)

            # Случайные движения мыши
            for _ in range(random.randint(2, 5)):
                x = random.randint(50, max_x)
                y = random.randint(50, max_y)
                try:
                    actions.move_by_offset(x, y).perform()
                    time.sleep(random.uniform(0.5, 1.5))
                    actions.reset_actions()  # Сброс действий
                except Exception as e:
                    print(f"Ошибка движения мыши в позиции ({x}, {y}): {e}")
                    continue

            # Плавная прокрутка
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)

            scroll_height = self.driver.execute_script(
                "return document.body.scrollHeight;"
            )
            for i in range(3):
                scroll_to = (scroll_height / 3) * (i + 1)
                self.driver.execute_script(f"window.scrollTo(0, {scroll_to});")
                time.sleep(random.uniform(1, 2))

        except Exception as e:
            print(f"Критическая ошибка имитации действий: {e}")

    def run_search_and_save(self, search_query, max_pages=3):
        """Запуск полного процесса: поиск → парсинг → сохранение"""
        products_data = self.search_products(search_query, max_pages)
        saved_count = self.save_products_to_db(products_data)
        return saved_count, len(products_data)
