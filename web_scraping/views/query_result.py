from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from web_scraping.models import Searchers


@login_required(login_url="login")
def query_result(request, search_id):
    try:
        # Получаем объект поиска
        search = Searchers.objects.prefetch_related("products").get(
            id=search_id
        )

        # Получаем все найденные товары для этого поиска
        products = search.products.all().order_by("name")

        # Если товаров нет, можно добавить дополнительную логику
        if not products.exists():
            # Например, запустить парсинг заново или показать сообщение
            pass

        context = {
            "search": search,
            "products": products,
            "query": search.query,  # Добавляем сам поисковый запрос
        }

        return render(
            request,
            "web_scarping/search_results.html",
            context=context,
        )

    except Searchers.DoesNotExist:
        return redirect("query_list")

