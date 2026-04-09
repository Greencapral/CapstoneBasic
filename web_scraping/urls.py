from django.contrib import admin
from django.urls import path

from web_scraping.views import (
    index,
    about,
    search_results,
    query_list,
    query_result,
)

urlpatterns = [
    path("", index, name="index"),
    path("about/", about, name="about"),
    path("query_list/", query_list, name="query_list"),
    path("search_results/",search_results, name="search_results_list",),
    path("search_results/<int:search_id>/", query_result, name="query_result",),
]
