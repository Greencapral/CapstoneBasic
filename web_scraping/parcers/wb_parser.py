from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import (
    expected_conditions as EC,
)

from decimal import Decimal, InvalidOperation
import re
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)

def search_products_wb(parser, search_query):

    products_data = []

    try:
        search_url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={search_query}"

        print(f"Открываем URL: {search_url}")
        parser.driver.get(search_url)

        WebDriverWait(parser.driver, 50).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print("Страница загружена успешно")
        print(f"Парсинг страницы...")

        WebDriverWait(parser.driver, 50).until(
            lambda driver: len(
                driver.find_elements(
                    By.CSS_SELECTOR,
                    ".product-card",
                )
            )
                           > 0
        )
        print("Карточки товаров загружены")

        page_products = _parse_current_page(parser)
        products_data.extend(page_products)
        print(f"Найдено товаров на странице: {len(page_products)}")

    except WebDriverException as e:
        print(f"Ошибка WebDriver: {e}")
    except TimeoutException as e:
        print(f"Таймаут ожидания: {e}")
    except Exception as e:
        print(f"Критическая ошибка при парсинге: {e}")
    finally:
        parser.close()

    return products_data


def _parse_current_page(parser):
    products = []
    try:
        WebDriverWait(parser.driver, 15).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, ".product-card")
            )
        )
        product_cards = parser.driver.find_elements(
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
                                abs(hash(product_url)) % (10 ** 8)
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
