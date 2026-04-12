from celery import shared_task
from web_scraping.models import Searchers, Product
from web_scraping.services import ozon_service, wildberries_service



@shared_task(bind=True)
def scrape_marketplace_task(self, marketplace_name, query, search_id):
    """
    Асинхронная задача Celery для парсинга товаров с маркетплейсов по поисковому запросу.
    Выполняет парсинг на Ozon или Wildberries, сохраняет найденные товары в БД,
    обновляет статус выполнения задачи через self.update_state().

    Args:
        self (Task): экземпляр задачи Celery (требуется из‑за bind=True).
        marketplace_name (str): домен маркетплейса ('ozon.ru' или 'wildberries.ru').
        query (str): поисковый запрос для парсинга.
        search_id (int): идентификатор записи поиска в БД.

    Returns:
        dict: словарь с результатами парсинга:
            - marketplace (str): название маркетплейса;
            - product_ids (list): список ID найденных товаров;
            - status (str): статус выполнения ('success').

    Raises:
        Exception: перебрасывается после логирования ошибки в состоянии FAILURE.
    """
    try:
        # Уведомляем о начале выполнения задачи (0% прогресса)
        self.update_state(
            state='PROGRESS',
            meta={'progress': 0, 'status': 'Инициализация...'}
        )

        # Обновляем статус: подготовка к парсингу (10% прогресса)
        self.update_state(
            state='PROGRESS',
            meta={'progress': 10, 'status': 'Подготовка...'}
        )

        # Выполняем парсинг в зависимости от указанного маркетплейса
        if marketplace_name == 'ozon.ru':
            # Уведомляем, что начался парсинг Ozon (20% прогресса)
            self.update_state(
                state='PROGRESS',
                meta={'progress': 20, 'status': 'Парсим Ozon...'}
            )
            # Вызываем сервис парсинга Ozon в headless‑режиме
            result = ozon_service.scrape_ozon(search_query=query, headless=True)
        elif marketplace_name == 'wildberries.ru':
            # Уведомляем, что начался парсинг Wildberries (20% прогресса)
            self.update_state(
                state='PROGRESS',
                meta={'progress': 20, 'status': 'Парсим Wildberries...'}
            )
            # Вызываем сервис парсинга Wildberries в headless‑режиме
            result = wildberries_service.scrape_wb(search_query=query, headless=True)

        # Уведомляем, что идёт обработка полученных данных (80% прогресса)
        self.update_state(
            state='PROGRESS',
            meta={'progress': 80, 'status': 'Обработка данных...'}
        )

        # Извлекаем список ID найденных товаров из результата парсинга
        product_ids = result.get('product_ids', [])

        # Получаем запись поиска из БД по ID
        search = Searchers.objects.get(id=search_id)
        # Получаем текущие ID товаров, уже связанных с этим поиском
        existing_ids = list(search.products.values_list('product_id', flat=True))
        # Объединяем существующие и новые ID, убираем дубликаты
        all_ids = list(set(existing_ids + product_ids))

        # Связываем поиск с полным набором товаров (существующих и новых)
        search.products.set(
            Product.objects.filter(product_id__in=all_ids)
        )

        # Уведомляем об успешном завершении задачи (100% прогресса)
        self.update_state(
            state='SUCCESS',
            meta={
                'progress': 100,
                'status': f'Завершено! Найдено {len(product_ids)} товаров',
                'product_ids': product_ids
            }
        )

        # Возвращаем итоговый результат задачи
        return {
            'marketplace': marketplace_name,
            'product_ids': product_ids,
            'status': 'success'
        }

    except Exception as e:
        # При ошибке уведомляем о сбое (0% прогресса), логируем сообщение
        self.update_state(
            state='FAILURE',
            meta={
                'progress': 0,
                'status': f'Ошибка: {str(e)}',
                'product_ids': []
            }
        )
        # Перебрасываем исключение для обработки на уровне вызывающего кода
        raise
