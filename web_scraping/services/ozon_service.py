import random
import time

from web_scraping.parcers import Parser, search_products_ozon


def scrape_ozon(search_query, headless=False):
    """
    Выполняет полный цикл парсинга товаров с Ozon по заданному поисковому запросу.
    Создаёт экземпляр парсера, настраивает драйвер браузера, выполняет поиск товаров,
    сохраняет результаты в базу данных и возвращает сводную статистику.

    Args:
        search_query (str): Поисковый запрос для Ozon (например, «смартфон», «книга»).
        headless (bool, optional): Флаг запуска браузера в headless‑режиме
            (без графического интерфейса). По умолчанию False (режим с отображением окна).

    Returns:
        dict: Словарь с результатами операции, содержащий:
            - 'saved_count' (int): количество товаров, успешно сохранённых или обновлённых в БД;
            - 'total_found' (int): общее количество товаров, найденных в результате поиска;
            - 'search_query' (str): исходный поисковый запрос;
            - 'product_ids' (list): список ID всех обработанных товаров (для дальнейшего использования).
    """
    # Создаём экземпляр парсера для Ozon с указанием имени маркетплейса и режима запуска
    parser = Parser(name_mp="ozon.ru", headless=headless)

    # Инициализируем WebDriver браузера (настраиваем опции и запускаем браузер)
    parser.setup_driver()

    # Выполняем поиск товаров на Ozon по переданному поисковому запросу
    products_data = search_products_ozon(parser, search_query)

    # Сохраняем полученные данные о товарах в базу данных
    # Метод возвращает словарь с результатами сохранения (количество сохранённых, ID и т.д.)
    save_result = parser.save_products_to_db(products_data)

    # Формируем итоговый словарь с результатами для возврата
    return {
        "saved_count": save_result['saved_count'],  # Количество товаров, сохранённых/обновлённых в БД
        "total_found": len(products_data),  # Общее количество найденных товаров
        "search_query": search_query,  # Исходный поисковый запрос — для отчётности и анализа
        "product_ids": save_result['product_ids']  # Список ID всех обработанных товаров
    }

