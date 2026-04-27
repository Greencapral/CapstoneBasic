from django.urls import path

from web_scraping.views import (
    index,
    about,
    search_results,
    query_list,
    query_result,
    get_progress,
    query_progress,
)

# Список URL‑маршрутов для приложения веб‑скрапинга (web_scraping).
# Определяет соответствие между URL‑адресами и функциями представлений (views),
# обрабатывающими HTTP‑запросы. Каждый маршрут имеет символьное имя для удобной
# генерации ссылок в шаблонах и коде (через reverse() или {% url %}).
urlpatterns = [
    # Главная страница приложения.
    #
    # Связывает корневой URL ("/") с функцией представления index.
    # Параметры:
    # - "": пустой шаблон — соответствует корневому пути сайта.
    # - index: функция представления, отображающая главную страницу.
    # - name="index": имя маршрута для генерации URL (например, reverse("index")).
    path("", index, name="index"),

    # Страница «О проекте».
    # Отображает информационную страницу о функционале и назначении приложения.
    # - "about/": URL вида <домен>/about/.
    # - about: функция представления для страницы «О проекте».
    # - name="about": имя маршрута (reverse("about")).
    path("about/", about, name="about"),

    # Список поисковых запросов пользователя.
    # Показывает историю или текущий набор поисковых запросов, созданных пользователем.
    # - "query_list/": URL <домен>/query_list/.
    # - query_list: представление для отображения списка запросов.
    # - name="query_list": имя маршрута.
    path("query_list/", query_list, name="query_list"),

    # Общий список результатов поиска.
    # Отображает сводку всех результатов поиска по разным запросам.
    # - "search_results/": URL <домен>/search_results/.
    # - search_results: представление, формирующее список результатов.
    # - name="search_results_list": имя маршрута для ссылок.
    path("search_results/", search_results, name="search_results_list"),

    # Детали конкретного результата поиска по ID запроса.
    # Показывает детальные данные по одному поисковому запросу.
    # - "search_results/<int:search_id>/": URL с параметром search_id
    #   (например, /search_results/123/). Параметр передаётся в view как целое число.
    # - query_result: представление, обрабатывающее запрос по ID.
    # - name="query_result": имя маршрута.
    path("search_results/<int:search_id>/", query_result, name="query_result"),

    # API‑эндпоинт для получения прогресса выполнения поиска.
    # Возвращает текущее состояние (процент выполнения) поискового процесса.
    # Используется, для AJAX‑запросов от фронтенда.
    # - "get_progress/<int:search_id>/": URL с ID запроса (например, /get_progress/123/).
    # - get_progress: представление, возвращающее JSON с прогрессом.
    # - name="get_progress": имя маршрута.
    path("get_progress/<int:search_id>/", get_progress, name="get_progress"),

    # Страница прогресса выполнения поискового запроса.
    #
    # Отображает интерфейс отслеживания прогресса (например, прогресс‑бар)
    # для конкретного поискового задания.
    # - "progress/<int:search_id>/": URL вида /progress/123/.
    # - query_progress: представление с UI прогресса.
    # - name="query_progress": имя маршрута.
    path("progress/<int:search_id>/", query_progress, name="query_progress"),
]
