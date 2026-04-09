from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import (
    expected_conditions as EC,
)

from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from decimal import Decimal, InvalidOperation
import re



def search_products_ozon(parser, search_query):

    products_data = []
    try:
        search_url = f"https://www.ozon.ru/search/?text={search_query}"
        print(f"Открываем URL: {search_url}")

        parser.human_like_actions()
        parser.driver.get(search_url)

        try:
            WebDriverWait(parser.driver, 30).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR,
                     "span.c35_3_15-a1.tsHeadline500Medium"
                     )
                )
            )
            print("Все элементы с ценами загружены")
        except TimeoutException:
            print("Таймаут ожидания загрузки цен — продолжаем парсинг с доступными данными")


        print(f"Парсинг страницы...")

        WebDriverWait(parser.driver, 50).until(
            lambda driver: len(
                driver.find_elements(
                    By.CSS_SELECTOR,
                    "div.tile-root",
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
                (By.CSS_SELECTOR, "div.tile-root")
            )
        )
        WebDriverWait(parser.driver, 30).until(
            lambda driver: len(
                driver.find_elements(By.CSS_SELECTOR, "div.tile-root")
            )
                           > 0
        )

        product_cards = parser.driver.find_elements(
            By.CSS_SELECTOR, "div.tile-root"
        )
        print(f"Найдено карточек: {len(product_cards)}")

        for card in product_cards:
            try:
                product_id = "unknown"

                # Название товара
                try:
                    name_elem = card.find_element(
                        By.CSS_SELECTOR,
                        "span.tsBody500Medium",
                    )
                    full_text = name_elem.text.strip()

                    cleaned_name = full_text.replace("/", "").strip()
                    name = cleaned_name
                except NoSuchElementException:
                    print(
                        "Не найдено название товара, пропускаем карточку"
                    )

                # Цена
                try:
                    price_elem = card.find_element(
                        By.CSS_SELECTOR,
                        "span.c35_3_15-a1.tsHeadline500Medium",
                    )
                    price_text = price_elem.text.strip()  # «8 903 ₽»
                    if not price_text:
                        raise NoSuchElementException(
                            "Цена не найдена ни по одному селектору"
                        )

                    clean_price = re.sub(r"[^\d,.]", "", price_text)
                    clean_price = clean_price.replace(",", ".")

                    price = Decimal(clean_price)
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
                            r"(\d+)\/[^/]*\?at=",
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
