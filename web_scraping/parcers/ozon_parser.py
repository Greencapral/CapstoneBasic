
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from decimal import Decimal, InvalidOperation
import re
from config import celery_app

def search_products_ozon(parser, search_query):
    """
    Выполняет поиск и парсинг товаров на Ozon по заданному поисковому запросу.
    Открывает страницу поиска, ожидает загрузки ключевых элементов (цен и карточек товаров),
    парсит данные с текущей страницы и возвращает собранную информацию. Гарантированно
    закрывает WebDriver в блоке finally, даже при возникновении ошибок.

    Args:
        parser (object): Экземпляр парсера, содержащий инициализированный WebDriver
            и вспомогательные методы (например, human_like_actions).
        search_query (str): Текст поискового запроса, который будет отправлен на Ozon.

    Returns:
        list[dict]: Список словарей с данными о найденных товарах. Каждый словарь
            содержит следующие ключи:
            - 'name' (str): название товара;
            - 'price' (Decimal): цена товара;
            - 'product_id' (str): уникальный идентификатор товара;
            - 'image_url' (str or None): URL изображения товара;
            - 'url' (str): прямая ссылка на страницу товара на Ozon.
            Если произошла ошибка, возвращается пустой список.
    """
    products_data = []
    try:
        search_url = f"https://www.ozon.ru/search/?text={search_query}"
        print(f"Открываем URL: {search_url}")

        parser.human_like_actions()  # Имитация естественных действий пользователя (задержки, движение мыши и т. д.)
        parser.driver.get(search_url)  # Загрузка страницы поиска по сформированному URL

        try:
            # Ожидание видимости элементов с ценами (максимум 15 секунд)
            WebDriverWait(parser.driver, 15).until(
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

        page_products = _parse_current_page(parser)  # Вызов вспомогательной функции для парсинга товаров на текущей странице
        products_data.extend(page_products)  # Добавление полученных данных в общий список результатов
        print(f"Найдено товаров на странице: {len(page_products)}")

    except WebDriverException as e:
        print(f"Ошибка WebDriver: {e}")  # Обработка ошибок, специфичных для WebDriver (проблемы с драйвером, соединением и т. д.)
    except TimeoutException as e:
        print(f"Таймаут ожидания: {e}")  # Обработка таймаутов, которые не были перехвачены внутри блока try
    except Exception as e:
        print(f"Критическая ошибка при парсинге: {e}")  # Перехват всех остальных непредвиденных ошибок
    finally:
        parser.close()  # Гарантированное закрытие драйвера браузера, выполняется всегда, независимо от наличия ошибок

    return products_data


def _parse_current_page(parser):
    """
    Парсит данные о товарах с текущей страницы поиска Ozon.
    Ожидает загрузки карточек товаров, последовательно извлекает из каждой
    название, цену, ID, URL страницы товара и URL изображения. Для каждой
    карточки реализована отдельная обработка ошибок, чтобы не прерывать парсинг
    всей страницы при проблемах с одним элементом.

    Args:
        parser (object): Экземпляр парсера с активным WebDriver,
            настроенным на текущую страницу поиска Ozon.

    Returns:
        list[dict]: Список словарей с данными о товарах на странице.
            Каждый словарь содержит ключи:
            - 'name' (str): очищенное название товара;
            - 'price' (Decimal): цена товара (0.00 при ошибке парсинга);
            - 'product_id' (str): уникальный идентификатор товара (или сгенерированный хеш);
            - 'image_url' (str or None): URL изображения товара;
            - 'url' (str): прямая ссылка на страницу товара.
            При критических ошибках возвращается пустой список.
    """
    products = []
    try:
        product_cards = parser.driver.find_elements(
            By.CSS_SELECTOR, "div.tile-root"
        )  # Поиск всех карточек товаров на текущей странице
        print(f"Найдено карточек: {len(product_cards)}")

        for card in product_cards:
            try:
                product_id = "unknown"  # Значение по умолчанию, если ID не удалось извлечь

                # Название товара
                try:
                    name_elem = card.find_element(
                        By.CSS_SELECTOR,
                        "span.tsBody500Medium",)  # Поиск элемента с названием товара в текущей карточке
                    full_text = name_elem.text.strip()
                    cleaned_name = full_text.replace("/", "").strip()  # Удаление лишних символов и очистка строки
                    name = cleaned_name
                except NoSuchElementException:
                    print("Не найдено название товара, пропускаем карточку")
                    continue  # Пропускаем текущую карточку, если название не найдено

                # Цена товара
                try:
                    price_elem = card.find_element(
                        By.CSS_SELECTOR,
                        "span.c35_3_15-a1.tsHeadline500Medium",)  # Поиск элемента с ценой в текущей карточке
                    price_text = price_elem.text.strip()
                    if not price_text:
                        raise NoSuchElementException("Цена не найдена ни по одному селектору")

                    clean_price = re.sub(r"[^\d,.]", "", price_text)  # Оставляем только цифры, точки и запятые
                    clean_price = clean_price.replace(",", ".")  # Замена запятой на точку для корректного преобразования в Decimal
                    price = Decimal(clean_price)  # Преобразование строки в Decimal для точности расчётов
                except (ValueError, InvalidOperation, NoSuchElementException) as e:
                    print(f"Ошибка при парсинге цены: {e}")
                    price = Decimal("0.00")  # Значение по умолчанию при ошибке извлечения или преобразования цены

                # URL товара и извлечение ID
                try:
                    link_elem = card.find_element(
                        By.CSS_SELECTOR,
                        "a.tile-clickable-element",
                    )  # Поиск ссылки на страницу товара в текущей карточке
                    product_url = link_elem.get_attribute("href")  # Извлечение URL из атрибута href

                    # Извлекаем ID из URL с помощью регулярного выражения
                    if product_url:
                        product_id_match = re.search(
                            r"(\d+)\/[^/]*\?at=", product_url,)  # Регулярное выражение для поиска числового ID в URL
                        if product_id_match:
                            product_id = product_id_match.group(1)  # Извлекаем первую группу (ID) из совпадения
                        else:
                            # Альтернативный ID: генерируем хеш на основе URL (ограничиваем до 8 цифр)
                            hash_part = str(abs(hash(product_url)) % (10**5)).zfill(5)
                            product_id = "999" + hash_part
                            print(f"ID не найден в URL: {product_url}, сгенерирован ID: {product_id}")
                    else:
                        product_url = ""  # Если URL не найден, устанавливаем пустую строку
                except NoSuchElementException:
                    product_url = ""  # Если ссылка не найдена, оставляем URL пустым

                # Изображение товара
                try:
                    image_elem = card.find_element(
                        By.CSS_SELECTOR,
                        "img.b95_3_4-a",)  # Поиск элемента изображения в текущей карточке
                    image_url = image_elem.get_attribute("src")  # Извлечение URL изображения из атрибута src
                except NoSuchElementException:
                    image_url = None  # Если изображение не найдено, устанавливаем None

                print(f"Добавляем товар: ID={product_id}, название={name}, цена={price}")
                products.append({
                    "name": name,
                    "price": price,
                    "product_id": product_id,
                    "image_url": image_url,
                    "url": product_url,
                })  # Добавление данных о товаре в итоговый список

            except Exception as card_error:
                print(f"Ошибка при парсинге карточки: {card_error}")
                continue  # Продолжаем парсинг следующих карточек, несмотря на ошибку в текущей

    except Exception as e:
        print(f"Общая ошибка парсинга страницы: {e}")  # Обработка критических ошибок, прерывающих парсинг всей страницы

    return products
