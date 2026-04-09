from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from web_scraping.models import Searchers


@login_required(login_url="login")
def query_result(request, search_id):
    """
    Отображает результаты поиска товаров по сохранённому поисковому запросу.
    Позволяет фильтровать и сортировать товары по цене, названию и маркетплейсам.

    Args:
        request (HttpRequest): HTTP‑запрос от клиента, содержащий:
            - параметры сортировки и фильтрации (в GET‑параметрах);
            - информацию о пользователе (request.user).
        search_id (int): ID записи о поиске (Searchers) в базе данных.

    Returns:
        HttpResponse: Отрендеренный HTML‑шаблон web_scarping/search_results.html
            с контекстом, включающим результаты поиска, параметры фильтрации и сортировки.

    Raises:
        Searchers.DoesNotExist: Если запись о поиске с указанным ID не найдена —
            перенаправляет на страницу списка запросов (query_list).
    """
    try:
        # Получаем запись о поиске по ID с предварительной загрузкой связанных товаров
        # (prefetch_related оптимизирует запросы к БД при обращении к products)
        search = Searchers.objects.prefetch_related("products").get(id=search_id)

        # Извлекаем все товары, связанные с данной записью о поиске
        products = search.products.all()

        # Получаем параметр сортировки из GET‑запроса (по умолчанию — по названию)
        sort_by = request.GET.get('sort', 'name')
        # Применяем сортировку в зависимости от выбранного параметра
        if sort_by == 'price_asc':
            products = products.order_by('price')  # По возрастанию цены
        elif sort_by == 'price_desc':
            products = products.order_by('-price')  # По убыванию цены
        else:
            products = products.order_by('name')  # По названию (алфавитный порядок)

        # Получаем список выбранных маркетплейсов для фильтрации из GET‑параметров
        marketplace_filter = request.GET.getlist('marketplace')
        # Если фильтры по маркетплейсам указаны, применяем их к набору товаров
        if marketplace_filter:
            products = products.filter(marketplace__name__in=marketplace_filter)

        # Получаем минимальную и максимальную цену из GET‑параметров для фильтрации
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')

        # Если указана минимальная цена, преобразуем в число и фильтруем товары
        if min_price:
            try:
                min_price = float(min_price)  # Преобразуем строку в число с плавающей точкой
                products = products.filter(price__gte=min_price)  # Цена >= min_price
            except ValueError:
                pass  # Игнорируем ошибку преобразования (оставляем без фильтрации)

        # Если указана максимальная цена, преобразуем в число и фильтруем товары
        if max_price:
            try:
                max_price = float(max_price)  # Преобразуем строку в число с плавающей точкой
                products = products.filter(price__lte=max_price)  # Цена <= max_price
            except ValueError:
                pass  # Игнорируем ошибку преобразования (оставляем без фильтрации)

        # Формируем контекст для передачи в шаблон
        context = {
            "search": search,  # Запись о поиске (для отображения информации о запросе)
            "products": products,  # Отфильтрованный и отсортированный набор товаров
            "query": search.query,  # Исходный поисковый запрос
            "sort_by": sort_by,  # Текущий параметр сортировки
            "marketplace_filter": marketplace_filter,  # Выбранные маркетплейсы для фильтрации
            "min_price": min_price,  # Минимальная цена из фильтра
            "max_price": max_price,  # Максимальная цена из фильтра
        }

        # Рендерим HTML‑страницу с результатами поиска и параметрами фильтрации
        return render(
            request,
            "web_scarping/search_results.html",
            context=context,
        )

    except Searchers.DoesNotExist:
        # Если запись о поиске не найдена, перенаправляем на страницу списка запросов
        return redirect("query_list")
