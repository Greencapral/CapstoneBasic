import random
import time

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

from web_scraping.parcers import Parser


def search_products_wb(parser, search_query):
    """
    Выполняет поиск товаров на Wildberries по заданному запросу и парсит данные с первой страницы результатов.
    Открывает страницу поиска, ожидает загрузки элементов, извлекает данные о товарах
    с помощью вспомогательной функции _parse_current_page. Гарантированно закрывает
    драйвер в блоке finally, даже при возникновении ошибок.

    Args:
        parser (Parser): Экземпляр класса Parser с инициализированным WebDriver.
            Должен содержать атрибут driver (активный браузер).
        search_query (str): Поисковый запрос для Wildberries.

    Returns:
        list[dict]: Список словарей с данными о найденных товарах. Каждый словарь содержит
            информацию, извлечённую функцией _parse_current_page (название, цена, ID и т.д.).
            При ошибках возвращается пустой список.
    """
    products_data = []  # Инициализируем пустой список для хранения данных о товарах

    try:
        # Формируем URL для поиска на Wildberries с подстановкой поискового запроса
        search_url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={search_query}"


        print(f"Открываем URL: {search_url}")

        parser.driver.get("https://google.com")  # Первая вкладка

        # Открываем новую пустую вкладку через JS
        parser.driver.execute_script("window.open('');")

        # Получаем все дескрипторы окон
        window_handles = parser.driver.window_handles

        # Переключаемся на последнюю открытую вкладку (новую)
        parser.driver.switch_to.window(window_handles[-1])

        # Переходим на нужный URL во второй вкладке

        parser.driver.get("https://www.wildberries.ru")
        time.sleep(random.uniform(2, 4))

        parser.driver.get(search_url)  # Открываем сформированный URL в браузере

        # Ожидаем загрузки элемента body (максимум 20 секунд) как признак базовой загрузки страницы
        WebDriverWait(parser.driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print("Страница загружена успешно")
        parser.scroll_down_for_5_seconds()
        # parser.human_like_actions()  # Имитация естественных действий пользователя (задержки, движение мыши и т.д.)
        print(f"Парсинг страницы...")

        # Вызываем вспомогательную функцию для парсинга данных с текущей страницы
        page_products = _parse_current_page(parser)
        products_data.extend(page_products)  # Добавляем найденные товары в общий список
        print(f"Найдено товаров на странице: {len(page_products)}")

    except WebDriverException as e:
        print(f"Ошибка WebDriver: {e}")  # Обработка ошибок, связанных с работой браузера/драйвера
    except TimeoutException as e:
        print(f"Таймаут ожидания: {e}")  # Обработка таймаутов ожидания элементов
    except Exception as e:
        print(f"Критическая ошибка при парсинге: {e}")  # Перехват любых других непредвиденных ошибок
    finally:
        parser.close()  # Гарантированно закрываем драйвер, даже если произошла ошибка

    return products_data  # Возвращаем собранные данные о товарах (может быть пустым списком при ошибках)


def _parse_current_page(parser):
    """
    Парсит данные о товарах с текущей страницы Wildberries.
    Находит все карточки товаров (.product-card), извлекает из них:
    - название;
    - цену;
    - ID товара (из URL или генерирует);
    - URL товара;
    - ссылку на изображение.

    Обрабатывает возможные ошибки для каждой карточки отдельно, чтобы не прерывать
    парсинг всей страницы при проблемах с отдельным товаром.

    Args:
        parser (Parser): Экземпляр класса Parser с активным WebDriver.
            Должен содержать атрибут driver (браузер с открытой страницей Wildberries).

    Returns:
        list[dict]: Список словарей с данными о товарах. Каждый словарь содержит:
            - 'name' (str): название товара;
            - 'price' (Decimal): цена в формате Decimal (0.00 при ошибке);
            - 'product_id' (str): уникальный идентификатор товара;
            - 'image_url' (str or None): ссылка на изображение (None, если не найдено);
            - 'url' (str): URL страницы товара.
            При общей ошибке парсинга возвращается пустой список.
    """
    products = []  # Инициализируем пустой список для хранения данных о товарах

    try:
        # Ожидаем загрузки всех карточек товаров (максимум 15 секунд)
        WebDriverWait(parser.driver, 15).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, ".product-card")
            )
        )
        # Находим все элементы карточек товаров на странице
        product_cards = parser.driver.find_elements(
            By.CSS_SELECTOR, ".product-card"
        )
        print(f"Найдено карточек: {len(product_cards)}")

        for card in product_cards:  # Перебираем каждую карточку товара для парсинга
            try:
                product_id = "unknown"  # Инициализируем ID товара как неизвестный

                # Извлекаем название товара
                try:
                    name_elem = card.find_element(
                        By.CSS_SELECTOR,
                        ".product-card__name",
                    )
                    full_text = name_elem.text.strip()  # Получаем текст и убираем пробелы по краям

                    # Очищаем название от некорректных символов (например, слешей)
                    cleaned_name = full_text.replace("/", "").strip()
                    name = cleaned_name
                except NoSuchElementException:
                    print("Не найдено название товара, пропускаем карточку")
                    continue  # Пропускаем карточку, если название не найдено

                # Извлекаем цену товара
                try:
                    price_elem = card.find_element(
                        By.CSS_SELECTOR,
                        ".price__lower-price",
                    )
                    price_text = price_elem.text.strip()  # Получаем текст цены и убираем пробелы

                    # Очищаем строку цены от лишних символов (₽, пробелы, неразрывные пробелы)
                    clean_price = (
                        price_text.replace(" ₽", "")
                        .replace(" ", "")
                        .replace("\u00a0", "")
                    )

                    price = Decimal(clean_price)  # Преобразуем очищенную строку в Decimal
                except (ValueError, InvalidOperation, NoSuchElementException):
                    price = Decimal("0.00")  # Устанавливаем цену 0.00 при ошибках парсинга

                # Извлекаем URL товара и получаем ID из URL
                try:
                    link_elem = card.find_element(
                        By.CSS_SELECTOR,
                        ".product-card__link",
                    )
                    product_url = link_elem.get_attribute("href")  # Получаем атрибут href (URL)

                    if product_url:
                        # Ищем ID товара в URL по шаблону /catalog/(\d+)/
                        product_id_match = re.search(
                                r"/catalog/(\d+)/", product_url,)
                        if product_id_match:
                            product_id = product_id_match.group(1)  # Извлекаем ID из совпадения
                        else:
                            # Генерируем ID на основе хеша URL, если ID не найден в URL
                            product_id = str(
                                abs(hash(product_url)) % (10 ** 8)
                            )
                            print(
                                f"ID не найден в URL: {product_url}, сгенерирован ID: {product_id}"
                            )
                    else:
                        product_url = ""  # Если URL не найден, устанавливаем пустую строку
                except NoSuchElementException:
                    product_url = ""  # При отсутствии элемента устанавливаем пустую строку для URL

                # Извлекаем ссылку на изображение товара
                try:
                    image_elem = card.find_element(
                        By.CSS_SELECTOR,
                        ".product-card__img-wrap .j-thumbnail",
                    )
                    image_url = image_elem.get_attribute("src")  # Получаем атрибут src (URL изображения)
                except NoSuchElementException:
                    image_url = None  # Если изображение не найдено, устанавливаем None
                    # Выводим информацию о добавляемом товаре для отладки
                    print(
                        f"Добавляем товар: ID={product_id}, название={name}, цена={price}")
                # Добавляем словарь с данными товара в общий список
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
                continue  # Пропускаем текущую карточку при любой ошибке парсинга

    except Exception as e:
        print(f"Общая ошибка парсинга страницы: {e}")  # Выводим сообщение об общей ошибке парсинга

    return products  # Возвращаем список собранных данных о товарах (может быть пустым при ошибках)