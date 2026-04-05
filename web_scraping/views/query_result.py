from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from web_scraping.models import Searchers


# @login_required(login_url="login")
# def query_result(request, search_id):
#     try:
#         # Получаем объект поиска
#         search = Searchers.objects.prefetch_related("products").get(
#             id=search_id
#         )
#
#         # Получаем все найденные товары для этого поиска
#         products = search.products.all().order_by("name")
#
#         # Если товаров нет, можно добавить дополнительную логику
#         if not products.exists():
#             # Например, запустить парсинг заново или показать сообщение
#             pass
#
#         context = {
#             "search": search,
#             "products": products,
#             "query": search.query,  # Добавляем сам поисковый запрос
#         }
#
#         return render(
#             request,
#             "web_scarping/search_results.html",
#             context=context,
#         )
#
#     except Searchers.DoesNotExist:
#         return redirect("query_list")

@login_required(login_url="login")
def query_result(request, search_id):
    try:
        # Получаем объект поиска
        search = Searchers.objects.prefetch_related("products").get(id=search_id)

        # Получаем все найденные товары для этого поиска
        products = search.products.all()

        # Сортировка
        sort_by = request.GET.get('sort', 'name')  # по умолчанию — по названию
        if sort_by == 'price_asc':
            products = products.order_by('price')
        elif sort_by == 'price_desc':
            products = products.order_by('-price')
        else:
            products = products.order_by('name')

        # Фильтрация по площадке
        marketplace_filter = request.GET.getlist('marketplace')  # ['ozon', 'wb']
        if marketplace_filter:
            products = products.filter(marketplace__name__in=marketplace_filter)

        # Фильтрация по цене
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')

        if min_price:
            try:
                min_price = float(min_price)
                products = products.filter(price__gte=min_price)
            except ValueError:
                pass  # игнорируем некорректные значения

        if max_price:
            try:
                max_price = float(max_price)
                products = products.filter(price__lte=max_price)
            except ValueError:
                pass

        context = {
            "search": search,
            "products": products,
            "query": search.query,
            # Передаём параметры в шаблон для сохранения состояния фильтров
            "sort_by": sort_by,
            "marketplace_filter": marketplace_filter,
            "min_price": min_price,
            "max_price": max_price,
        }

        return render(
            request,
            "web_scarping/search_results.html",
            context=context,
        )

    except Searchers.DoesNotExist:
        return redirect("query_list")


