__all__ = {
    "index",
    "about",
    "search_results",
    "query_list",
    "query_result",
    "get_progress",
    "query_progress",
}

from web_scraping.views.index import index
from web_scraping.views.about import about
from web_scraping.views.search_results import (
    search_results,
)
from web_scraping.views.query_list import query_list
from web_scraping.views.query_result import query_result
from web_scraping.views.query_progress import query_progress
from web_scraping.views.get_progress import get_progress