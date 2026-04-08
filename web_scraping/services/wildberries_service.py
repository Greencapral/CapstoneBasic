from web_scraping.parcers import Parser, search_products_wb


def scrape_wb(search_query, headless=False):
    parser = Parser(name_mp="wildberries.ru", headless=headless)
    parser.setup_driver()

    products_data = search_products_wb(parser,search_query)
    save_result = parser.save_products_to_db(products_data)
    return {
        "saved_count": save_result['saved_count'],
        "total_found": len(products_data),
        "search_query": search_query,
        "product_ids": save_result['product_ids']
    }