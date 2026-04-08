__all__ = {
    "Parser",
    "search_products_wb",
    "search_products_ozon",
}

from web_scraping.parcers.parser_base import Parser
from web_scraping.parcers.wb_parser import search_products_wb
from web_scraping.parcers.ozon_parser import search_products_ozon