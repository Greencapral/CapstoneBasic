# services/wildberries_service.py
from web_scraping.parcers.wildberries_parser import (
    WildberriesParser,
)


class WildberriesScrapingService:
    @staticmethod
    def scrape_wildberries(
        search_query, max_pages=3, headless=False
    ):
        """Сервис для запуска парсинга Wildberries"""
        parser = WildberriesParser(headless=headless)
        saved_count, total_found = (
            parser.run_search_and_save(
                search_query, max_pages
            )
        )

        return {
            "saved_count": saved_count,
            "total_found": total_found,
            "search_query": search_query,
        }
