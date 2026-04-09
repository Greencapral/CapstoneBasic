from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from web_scraping.models import Product, Marketplace


def search_results(request):
    """
    Обрабатывает поиск товаров по названию с возможностью фильтрации по маркетплейсам.
    Выполняет поиск товаров, содержащих поисковый запрос в названии, с опциональной
    фильтрацией по выбранным маркетплейсам. Отображает результаты на странице.

    Args:
        request (HttpRequest): HTTP‑запрос от клиента, содержащий:
            - поисковый запрос (в параметре 'query');
            - выбранные маркетплейсы для фильтрации (в 'marketplaces[]');
            - информацию о пользователе (request.user).

    Returns:
        HttpResponse: Отрендеренный HTML‑шаблон web_scarping/search_results.html
            с контекстом, включающим найденные товары, параметры поиска и список маркетплейсов.
    """
    # Получаем поисковый запрос из GET‑параметров (по умолчанию — пустая строка)
    # и убираем лишние пробелы по краям
    query = request.GET.get("query", "").strip()

    # Получаем список выбранных маркетплейсов из GET‑параметров
    marketplaces = request.GET.getlist("marketplaces[]")

    # Получаем все доступные маркетплейсы для отображения в фильтре выбора
    all_marketplaces = Marketplace.objects.all()

    # Инициализируем пустой список для хранения ID найденных маркетплейсов
    marketplace_ids = []

    # Перебираем названия маркетплейсов из запроса и получаем их ID из БД
    for marketplace_name in marketplaces:
        try:
            # Ищем маркетплейс в БД по точному совпадению имени
            marketplace = Marketplace.objects.get(name=marketplace_name)
            # Добавляем ID найденного маркетплейса в список для последующей фильтрации
            marketplace_ids.append(marketplace.pk)
        except ObjectDoesNotExist:
            # Если маркетплейс не найден в БД, пропускаем его (игнорируем ошибку)
            pass


    # Выполняем поиск товаров, название которых содержит поисковый запрос
    # (без учёта регистра благодаря icontains)
    products = Product.objects.filter(name__icontains=query)

    # Если выбраны маркетплейсы для фильтрации, применяем фильтр по ID маркетплейсов
    if marketplace_ids:
        products = products.filter(marketplace__in=marketplace_ids)

    # Формируем контекст для передачи в шаблон
    context = {
        "products": products,  # Найденные товары (отфильтрованные по запросу и маркетплейсам)
        "query": query,  # Исходный поисковый запрос — для отображения в интерфейсе и сохранения в форме
        "all_marketplaces": all_marketplaces,  # Все доступные маркетплейсы — для отображения списка фильтров
        "selected_marketplaces": marketplaces,  # Выбранные пользователем маркетплейсы — для отметки в интерфейсе
    }

    # Рендерим HTML‑страницу с результатами поиска и параметрами фильтрации
    return render(
        request,
        "web_scarping/search_results.html",
        context=context,
    )
