from web_scraping.ozon_parser import (
    OzonParser,
)


class OzonScrapingService:
    @staticmethod
    def scrape_ozon(
        search_query, max_pages=3, headless=False
    ):
        """Сервис для запуска парсинга Ozon"""
        parser = OzonParser(headless=headless)
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
