from django.contrib import admin
from django.urls import path

from web_scraping.views import index, about, search_results,query_list

urlpatterns = [
    path("", index, name="index"),
    path("about/", about, name="about"),
    path("search_results/", search_results, name="search_results"),
    path("query_list/",query_list,name="query_list"),
]
