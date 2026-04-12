from celery import shared_task
from web_scraping.models import Searchers, Product
from web_scraping.services import ozon_service, wildberries_service


@shared_task(bind=True)
def scrape_marketplace_task(self, marketplace_name, query, search_id):
    try:
        # Начальный прогресс
        self.update_state(
            state='PROGRESS',
            meta={'progress': 0, 'status': 'Инициализация...'}
        )

        # Подготовка
        self.update_state(
            state='PROGRESS',
            meta={'progress': 10, 'status': 'Подготовка...'}
        )

        # Парсинг
        if marketplace_name == 'ozon.ru':
            self.update_state(
                state='PROGRESS',
                meta={'progress': 20, 'status': 'Парсим Ozon...'}
            )
            result = ozon_service.scrape_ozon(search_query=query, headless=True)
        elif marketplace_name == 'wildberries.ru':
            self.update_state(
                state='PROGRESS',
                meta={'progress': 20, 'status': 'Парсим Wildberries...'}
            )
            result = wildberries_service.scrape_wb(search_query=query, headless=True)

        # Обработка результатов
        self.update_state(
            state='PROGRESS',
            meta={'progress': 80, 'status': 'Обработка данных...'}
        )

        product_ids = result.get('product_ids', [])

        # Обновление БД
        search = Searchers.objects.get(id=search_id)
        existing_ids = list(search.products.values_list('product_id', flat=True))
        all_ids = list(set(existing_ids + product_ids))

        search.products.set(
            Product.objects.filter(product_id__in=all_ids)
        )

        # Финальный прогресс
        self.update_state(
            state='SUCCESS',
            meta={
                'progress': 100,
                'status': f'Завершено! Найдено {len(product_ids)} товаров',
                'product_ids': product_ids
            }
        )

        return {
            'marketplace': marketplace_name,
            'product_ids': product_ids,
            'status': 'success'
        }

    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={
                'progress': 0,
                'status': f'Ошибка: {str(e)}',
                'product_ids': []
            }
        )
        raise