from web_scraping.parcers.wildberries_parser import (
    WildberriesParser,
)


class WildberriesScrapingService:
    @staticmethod
    def scrape_wildberries(search_query, max_pages=1, headless=False):
        parser = WildberriesParser(headless=headless)
        print('Test2?')
        saved_count, total_found, product_ids = parser.run_search_and_save(search_query, max_pages)
        return {
            "saved_count": saved_count,
            "total_found": total_found,
            "search_query": search_query,
            "product_ids": product_ids
        }

    # @staticmethod
    # def scrape_wildberries(search_query, max_pages=3, headless=False):
    #     parser = WildberriesParser(headless=headless)
    #     saved_count, total_found = parser.run_search_and_save(
    #         search_query, max_pages
    #     )
    #
    #     return {
    #         "saved_count": saved_count,
    #         "total_found": total_found,
    #         "search_query": search_query,
    #     }
