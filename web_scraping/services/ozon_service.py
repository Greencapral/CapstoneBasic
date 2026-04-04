from web_scraping.parcers.ozon_parser import (
    OzonParser,
)


class OzonScrapingService:
    @staticmethod
    def scrape_ozon(search_query, max_pages=1, headless=False):
        """Сервис для запуска парсинга Ozon"""
        parser = OzonParser(headless=headless)
        print('Test2_2?')
        saved_count, total_found, product_ids = parser.run_search_and_save(
            search_query, max_pages
        )

        return {
            "saved_count": saved_count,
            "total_found": total_found,
            "search_query": search_query,
            "product_ids": product_ids
        }
