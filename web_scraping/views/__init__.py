__all__ = {
    "index",
    "about",
    "search_results",
    "query_list",
    "query_result",
    "query_progress",
    "get_progress",
}

from web_scraping.views.index import index
from web_scraping.views.about import about
from web_scraping.views.search_results import (
    search_results,
)
from web_scraping.views.query_list import query_list, query_progress, get_progress
from web_scraping.views.query_result import query_result