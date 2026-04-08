from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import (
    expected_conditions as EC,
)
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from decimal import Decimal, InvalidOperation
import time
import re
from django.db import transaction
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)

from web_scraping.models import (
    Product,
    Marketplace,
)  # Замените your_app на имя вашего приложения
from config import is_docker_container

class WildberriesParser:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.marketplace = None
        self.search_query = None

    def setup_driver(self):
        options = Options()
        if self.headless:
            options.add_argument("--headless")

        # Базовые опции для обхода защиты
        options.add_argument("--no-sandbox")#
        options.add_argument("--disable-dev-shm-usage")#
        options.add_argument("--disable-blink-features=AutomationControlled")#
        options.add_experimental_option(
            "excludeSwitches", ["enable-automation"]
        )#
        options.add_experimental_option("useAutomationExtension", False)#

        # Дополнительные опции для маскировки
        options.add_argument("--disable-extensions")#
        options.add_argument("--disable-plugins")#
        options.add_argument("--disable-popup-blocking")#
        options.add_argument("--profile-directory=Default")#
        options.add_argument("--disable-background-timer-throttling")#
        options.add_argument("--disable-backgrounding-occluded-windows")#
        options.add_argument("--disable-renderer-backgrounding")#

        # Разрешение экрана и User-Agent
        options.add_argument("--window-size=1920,1080")
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        options.add_argument(f"--user-agent={user_agent}")

        try:
            service = Service(ChromeDriverManager().install())
            if is_docker_container():
                self.driver = webdriver.Remote(command_executor='http://selenium:4444/wd/hub', options=options)
            else:
                self.driver = webdriver.Chrome(service=service, options=options)

            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => false});"
            )

            self.marketplace = Marketplace.objects.get(name="wildberries.ru")
            print(
                f"Marketplace найден: {self.marketplace}, ID: {self.marketplace.pk}"
            )
        except Exception as e:
            print(f"Ошибка инициализации драйвера: {e}")
            raise

    def search_products(self, search_query, max_pages=3):
        if not self.driver:
            self.setup_driver()

        products_data = []

        try:
            search_url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={search_query}"

            print(f"Открываем URL: {search_url}")
            self.driver.get(search_url)

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
                            ".product-card",
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
        products = []
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, ".product-card")
                )
            )
            product_cards = self.driver.find_elements(
                By.CSS_SELECTOR, ".product-card"
            )
            print(f"Найдено карточек: {len(product_cards)}")

            for card in product_cards:
                try:
                    # Инициализируем product_id заранее
                    product_id = "unknown"

                    # Название товара
                    try:
                        name_elem = card.find_element(
                            By.CSS_SELECTOR,
                            ".product-card__name",
                        )
                        full_text = name_elem.text.strip()

                        # Очищаем от разделителя «/» и лишних пробелов
                        cleaned_name = full_text.replace("/", "").strip()
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
                            ".price__lower-price",
                        )
                        price_text = price_elem.text.strip()  # «8 903 ₽»

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
                            ".product-card__link",
                        )
                        product_url = link_elem.get_attribute("href")

                        # Извлекаем ID из URL
                        if product_url:
                            product_id_match = re.search(
                                r"/catalog/(\d+)/",
                                product_url,
                            )
                            if product_id_match:
                                product_id = product_id_match.group(1)
                            else:
                                # Альтернативный ID: хеш от URL (ограничиваем до 8 цифр)
                                product_id = str(
                                    abs(hash(product_url)) % (10**8)
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
                            ".product-card__img-wrap .j-thumbnail",
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
        saved_count = 0
        all_product_ids = []

        if self.marketplace is None:
            print(
                "Ошибка: marketplace не инициализирован. Запускаем setup_driver()"
            )
            self.setup_driver()

        for product_data in products_data:
            try:
                all_product_ids.append(product_data["product_id"])
                try:
                    existing_product = Product.objects.get(
                        product_id=product_data["product_id"],
                        marketplace=self.marketplace,
                    )
                    if existing_product.price == product_data["price"]:
                        print(
                            f"Цена не изменилась для товара '{product_data['name']}' (ID: {product_data['product_id']}), пропускаем сохранение"
                        )
                        continue
                    else:
                        print(
                            f"Цена изменилась для товара '{product_data['name']}' (ID: {product_data['product_id']}): "
                            f"{existing_product.price} → {product_data['price']}"
                        )
                        # Обновляем только нужные поля
                        existing_product.name = product_data["name"]
                        existing_product.image_url = product_data.get("image_url")
                        existing_product.url = product_data.get("url")
                        existing_product.price = product_data["price"]
                        existing_product.save()
                        saved_count += 1

                except Product.DoesNotExist:
                    new_product = Product.objects.create(
                        product_id=product_data["product_id"],
                        marketplace=self.marketplace,
                        name=product_data["name"],
                        price=product_data["price"],
                        image_url=product_data.get("image_url"),
                        url=product_data.get("url"),
                    )
                    saved_count += 1
                    print(
                        f"Добавлен новый товар: '{product_data['name']}' (ID: {product_data['product_id']})"
                    )

                except Exception as save_error:
                    print(
                        f"Ошибка сохранения товара {product_data.get('name', 'Unknown')}: {save_error}"
                    )
                    continue

            except Exception as e:
                print(f"Ошибка обработки товара: {e}")
                continue
        print(f"Успешно сохранено/обновлено {saved_count} товаров")
        return {
            "saved_count": saved_count,
            "total_found": len(products_data),
            "search_query": self.search_query,
            "product_ids": all_product_ids
        }

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def run_search_and_save(self, search_query, max_pages=3):
        print('Test3?')
        products_data = self.search_products(search_query, max_pages)

        save_result = self.save_products_to_db(products_data)

        return (
            save_result['saved_count'],
            len(products_data),
            save_result['product_ids']
        )

