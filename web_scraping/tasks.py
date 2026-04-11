from celery import shared_task
from web_scraping.models import Searchers, Product
from web_scraping.services import ozon_service, wildberries_service

@shared_task(bind=True)
def scrape_marketplace_task(self, marketplace_name, query, search_id):
    """
    Задача для парсинга одного маркетплейса с отслеживанием прогресса.
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'progress': 10, 'status': 'Начинаем парсинг...'}
        )

        if marketplace_name == 'ozon.ru':
            self.update_state(
                state='PROGRESS',
                meta={'progress': 30, 'status': 'Парсим Ozon...'}
            )
            result = ozon_service.scrape_ozon(search_query=query, headless=True)
        elif marketplace_name == 'wildberries.ru':
            self.update_state(
                state='PROGRESS',
                meta={'progress': 30, 'status': 'Парсим Wildberries...'}
            )
            result = wildberries_service.scrape_wb(search_query=query, headless=True)
        else:
            return {'status': 'unknown marketplace', 'product_ids': []}

        product_ids = result.get('product_ids', [])

        # Обновляем запись поиска
        search = Searchers.objects.get(id=search_id)
        existing_ids = list(search.products.values_list('product_id', flat=True))
        all_ids = list(set(existing_ids + product_ids))

        search.products.set(
            Product.objects.filter(product_id__in=all_ids)
        )

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
        return {
            'marketplace': marketplace_name,
            'product_ids': [],
            'status': 'error',
            'error': str(e)
        }
