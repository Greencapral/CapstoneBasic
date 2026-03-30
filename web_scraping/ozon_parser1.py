import random

from selenium import webdriver
from seleniumbase import SB
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import (
    expected_conditions as EC,
)
from selenium.webdriver.common.action_chains import ActionChains
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
# import undetected_chromedriver as uc


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
        options.add_argument(
            "--disable-blink-features=AutomationControlled"
        )
        options.add_experimental_option(
            "excludeSwitches", ["enable-automation"]
        )
        options.add_experimental_option(
            "useAutomationExtension", False
        )

        # Дополнительные опции для маскировки
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--profile-directory=Default")
        options.add_argument(
            "--disable-background-timer-throttling"
        )
        options.add_argument(
            "--disable-backgrounding-occluded-windows"
        )
        options.add_argument(
            "--disable-renderer-backgrounding"
        )

        # Разрешение экрана и User-Agent
        options.add_argument("--window-size=1920,1080")
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        options.add_argument(f"--user-agent={user_agent}")

        try:
            service = Service(
                ChromeDriverManager().install()
            )
            self.driver = webdriver.Chrome(
                service=service, options=options
            )
            # self.driver = uc.Chrome(options=options)

            # # Удаляем флаг WebDriver
            # self.driver.execute_script(
            #     "Object.defineProperty(navigator, 'webdriver', {get: () => false});"
            # )
            # Удаление признака автоматизации
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            self.marketplace = Marketplace.objects.get(
                name="ozon.ru"
            )
            print(
                f"Marketplace найден: {self.marketplace}, ID: {self.marketplace.id}"
            )
        except Exception as e:
            print(f"Ошибка инициализации драйвера: {e}")
            raise

    # def setup_driver(self):
    #     """Настройка драйвера через SeleniumBase с UC Mode"""
    #     try:
    #         sb_kwargs = {
    #             "uc": True,
    #             "headless": self.headless,
    #             "ad_block_on": True,
    #             "disable_csp": True,
    #         }
    #         # Создаём контекст для инициализации драйвера
    #         with SB(**sb_kwargs) as sb:
    #             self.sb = sb  # Сохраняем активный контекст
    #             self.driver = sb.driver  # Получаем драйвер внутри контекста
    #
    #             # Настройка User-Agent
    #             user_agent = (
    #                 "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    #                 "AppleWebKit/537.36 (KHTML, like Gecko) "
    #                 "Chrome/120.0.0.0 Safari/537.36"
    #             )
    #             self.driver.execute_cdp_cmd(
    #                 "Network.setUserAgentOverride",
    #                 {"userAgent": user_agent}
    #             )
    #
    #             self.marketplace = Marketplace.objects.get(name="ozon.ru")
    #             print(f"Marketplace найден: {self.marketplace}, ID: {self.marketplace.id}")
    #
    #     except Exception as e:
    #         print(f"Ошибка инициализации драйвера: {e}")
    #         raise

    def search_products(self, search_query, max_pages=3):
        """Поиск товаров с улучшенной обработкой ошибок"""
        if not self.driver:
            self.setup_driver()

        # if not self.sb:
        #     self.setup_driver()


        products_data = []
        try:
            # search_url = f"https://www.wildberries.ru/catalog/0/search?sort=popular&search={search_query}"
            search_url = f"https://www.ozon.ru/search/?text={search_query}"
            print(f"Открываем URL: {search_url}")

            self.human_like_actions()
            self.driver.get(search_url)

            # Ждём загрузки страницы
            WebDriverWait(self.driver, 50).until(
                EC.presence_of_element_located(
                    (By.TAG_NAME, "body")
                )
            )
            print("Страница загружена успешно")

            # # Используем UC Mode методы
            # self.sb.uc_open_with_reconnect(search_url, reconnect_time=4)
            # # Используем UC Mode методы через sb
            # self.sb.uc_open_with_reconnect(search_url, reconnect_time=4)
            #
            # print("Страница загружена успешно")


            for page in range(max_pages):
                print(f"Парсинг страницы {page + 1}...")

                WebDriverWait(self.driver, 50).until(
                    lambda driver: len(
                        driver.find_elements(
                            By.CSS_SELECTOR,
                            "span.tsBody500Medium",
                        )
                    )
                    > 0
                )
                print("Карточки товаров загружены")
                # # Улучшенное ожидание загрузки карточек
                # # self.sb.wait_for_element_visible(
                # self.sb.wait_for_element_visible(
                #     "a.tile-clickable-element",
                #     timeout=30
                # )
                # print("Карточки товаров загружены")


                page_products = self._parse_current_page()
                products_data.extend(page_products)
                print(
                    f"Найдено товаров на странице: {len(page_products)}"
                )

                # if not self._go_to_next_page():
                if not self._go_to_next_page():  # Передаём sb в метод
                    break
                time.sleep(3)

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
                    (By.CSS_SELECTOR, "a.tile-clickable-element")
                )
            )
            WebDriverWait(self.driver, 30).until(
                lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "a.tile-clickable-element")) > 0
            )
            # # Ждём загрузки карточек через SeleniumBase
            # # self.sb.wait_for_element_visible("a.tile-clickable-element", timeout=30)
            # self.sb.wait_for_element_visible("a.tile-clickable-element", timeout=30)

            product_cards = self.driver.find_elements(
                By.CSS_SELECTOR, "a.tile-clickable-element"
            )
            print(
                f"Найдено карточек: {len(product_cards)}"
            )

            for card in product_cards:
                try:
                    # Инициализируем product_id заранее
                    product_id = "unknown"

                    # Название товара
                    try:
                        name_elem = card.find_element(
                            By.CSS_SELECTOR,
                            "span.tsBody500Medium",
                        )
                        full_text = name_elem.text.strip()
                        print(full_text)

                        # Очищаем от разделителя «/» и лишних пробелов
                        cleaned_name = full_text.replace(
                            "/", ""
                        ).strip()
                        name = cleaned_name
                    except NoSuchElementException:
                        print(
                            "Не найдено название товара, пропускаем карточку"
                        )
                        continue  # пропускаем товар без названия

                    # Цена
                    try:
                        price_elem = card.find_element(
                            By.CSS_SELECTOR,
                            "span.tsHeadline500Medium",
                        )
                        price_text = (
                            price_elem.text.strip()
                        )  # «8 903 ₽»

                        # Очищаем текст: убираем символ ₽ и пробелы
                        clean_price = (
                            price_text.replace(" ₽", "")
                            .replace(" ", "")
                            .replace("\u00a0", "")
                        )  # \u00A0 — код &nbsp;

                        # Преобразуем в Decimal
                        price = Decimal(clean_price)
                    except (
                        ValueError,
                        InvalidOperation,
                        NoSuchElementException,
                    ):
                        price = Decimal("0.00")

                    # URL товара и извлечение ID
                    try:
                        link_elem = card.find_element(
                            By.CSS_SELECTOR,
                            "a.tile-clickable-element[target=\"_blank\"]",
                        )
                        product_url = (
                            link_elem.get_attribute("href")
                        )

                        # Извлекаем ID из URL
                        if product_url:
                            product_id_match = re.search(
                                r"/\/product\/[^\/]+\/(\d+)/",
                                product_url,
                            )
                            if product_id_match:
                                product_id = (
                                    product_id_match.group(
                                        1
                                    )
                                )
                            else:
                                # Альтернативный ID: хеш от URL (ограничиваем до 8 цифр)
                                product_id = str(
                                    abs(hash(product_url))
                                    % (10**8)
                                )
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
                            "a.tile-clickable-element img[loading=\"eager\"]",
                        )
                        image_url = (
                            image_elem.get_attribute("src")
                        )
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
                    print(
                        f"Ошибка при парсинге карточки: {card_error}"
                    )
                    continue
        except Exception as e:
            print(f"Общая ошибка парсинга страницы: {e}")

        return products

    def _go_to_next_page(self):
        """Переход на следующую страницу с улучшенной обработкой"""
        try:
            # Ищем кнопку следующей страницы через SeleniumBase
            if self.sb.is_element_visible(".pagination__next"):
                self.sb.click(".pagination__next")
                time.sleep(2)  # Ждём загрузки
                return True
            else:
                return False
        except (NoSuchElementException, TimeoutException):
            return False

    # @transaction.atomic
    # def save_products_to_db(self, products_data):
    #     """Сохранение данных в базу с обработкой дубликатов и проверкой изменения цены"""
    #     saved_count = 0
    #
    #     # Проверка, что marketplace корректно инициализирован
    #     if self.marketplace is None:
    #         print("Ошибка: marketplace не инициализирован. Запускаем setup_driver()")
    #         self.setup_driver()
    #
    #     for product_data in products_data:
    #         try:
    #             # Пытаемся найти существующий товар в базе
    #             try:
    #                 existing_product = Product.objects.get(
    #                     product_id=product_data["product_id"],
    #                     marketplace=self.marketplace
    #                 )
    #                 # Если товар найден, проверяем изменение цены
    #                 if existing_product.price == product_data["price"]:
    #                     # Цена не изменилась — пропускаем обновление
    #                     print(
    #                         f"Цена не изменилась для товара '{product_data['name']}' (ID: {product_data['product_id']}), пропускаем сохранение")
    #                     continue
    #                 else:
    #                     # Цена изменилась — обновляем остальные поля
    #                     print(
    #                         f"Цена изменилась для товара '{product_data['name']}' (ID: {product_data['product_id']}): "
    #                         f"{existing_product.price} → {product_data['price']}")
    #                     # Обновляем только нужные поля
    #                     existing_product.name = product_data["name"]
    #                 existing_product.image_url = product_data.get("image_url")
    #                 existing_product.url = product_data.get("url")
    #                 existing_product.price = product_data["price"]
    #                 existing_product.save()
    #                 saved_count += 1
    #
    #             except Product.DoesNotExist:
    #                 # Товар не найден в базе — создаём новый
    #                 Product.objects.create(
    #                     product_id=product_data["product_id"],
    #                     marketplace=self.marketplace,
    #                     name=product_data["name"],
    #                     price=product_data["price"],
    #                     image_url=product_data.get("image_url"),
    #                     url=product_data.get("url")
    #                 )
    #                 saved_count += 1
    #                 print(f"Добавлен новый товар: '{product_data['name']}' (ID: {product_data['product_id']})")
    #
    #         except Exception as save_error:
    #             print(
    #                 f"Ошибка сохранения товара {product_data.get('name', 'Unknown')}: {save_error}"
    #             )
    #         continue
    #
    #
    #     print(f"Успешно сохранено/обновлено {saved_count} товаров")
    #     return saved_count

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
                product, created = (
                    Product.objects.update_or_create(
                        product_id=product_data[
                            "product_id"
                        ],
                        marketplace=self.marketplace,
                        defaults={
                            "name": product_data["name"],
                            "price": product_data["price"],
                            "image_url": product_data.get(
                                "image_url"
                            ),
                            "url": product_data.get("url"),
                        },
                    )
                )
                if created:
                    saved_count += 1
            except Exception as save_error:
                print(
                    f"Ошибка сохранения товара {product_data.get('name', 'Unknown')}: {save_error}"
                )
                continue
        print(
            f"Успешно сохранено {saved_count} новых товаров"
        )
        return saved_count

    def close(self):
        """Безопасное закрытие драйвера"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
    # def close(self):
    #     """Безопасное закрытие драйвера"""
    #     if self.sb:
    #         try:
    #             self.sb.__exit__(None, None, None)
    #             self.driver = None
    #             self.sb = None
    #         except Exception as e:
    #             print(f"Ошибка закрытия драйвера: {e}")

    def human_like_actions(self):
        """Имитация человеческого поведения с учётом размера окна"""
        actions = ActionChains(self.driver)

        # Получаем размер окна браузера
        window_size = self.driver.get_window_size()
        max_x = window_size['width'] - 50  # отступ от края
        max_y = window_size['height'] - 50

        if max_x <= 0 or max_y <= 0:
            # Если окно слишком маленькое, используем стандартные значения
            max_x, max_y = 800, 600

        # Случайные движения мыши в пределах видимой области
        for _ in range(random.randint(2, 5)):
            x = random.randint(50, max_x)
            y = random.randint(50, max_y)
            try:
                actions.move_to_element_with_offset(
                    self.driver.find_element(By.TAG_NAME, "body"),
                    x, y
                ).perform()
                time.sleep(random.uniform(0.5, 1.5))
            except Exception as e:
                print(f"Ошибка движения мыши: {e}")
                # Возвращаем курсор в центр экрана
                actions.move_to_element_with_offset(
                    self.driver.find_element(By.TAG_NAME, "body"),
                    max_x // 2, max_y // 2
                ).perform()

        # Прокрутка страницы с плавным движением
        try:
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight/2);"
            )
            time.sleep(random.uniform(1, 3))

            # Дополнительная случайная прокрутка
            scroll_position = random.uniform(0.3, 0.7) * self.driver.execute_script(
                "return document.body.scrollHeight;")
            self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            time.sleep(random.uniform(1, 2))
        except Exception as e:
            print(f"Ошибка прокрутки: {e}")

    def run_search_and_save(
        self, search_query, max_pages=3
    ):
        """Запуск полного процесса: поиск → парсинг → сохранение"""
        products_data = self.search_products(
            search_query, max_pages
        )
        saved_count = self.save_products_to_db(
            products_data
        )
        return saved_count, len(products_data)
