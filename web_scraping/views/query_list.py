from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from web_scraping.models import Searchers,Marketplace,Product
from web_scraping.services import ozon_service, wildberries_service


@login_required(login_url="login")
def query_list(request):
    """
    Обрабатывает страницу списка поисковых запросов пользователя.
    Позволяет создавать новые поисковые запросы для маркетплейсов (Ozon, Wildberries),
    запускать парсинг товаров и отображает историю запросов пользователя.
    Для неавторизованных пользователей перенаправляет на страницу входа.

    Args:
        request (HttpRequest): HTTP‑запрос от клиента, содержащий:
            - метод запроса (GET/POST);
            - данные формы (при POST);
            - информацию о пользователе (request.user).

    Returns:
        HttpResponse: Отрендеренный HTML‑шаблон web_scarping/search_list.html
            с контекстом, включающим маркетплейсы, историю запросов и данные пользователя.
    """
    if request.method == 'POST':
        # Получаем поисковый запрос из данных формы (поле 'query')
        query = request.POST.get('query')
        # Получаем список выбранных маркетплейсов из формы (массив 'marketplaces[]')
        marketplace_domains = request.POST.getlist('marketplaces[]')

        # Проверяем, что запрос не пустой
        if not query:
            # Если запрос пустой, перенаправляем на ту же страницу
            return redirect('query_list')

        try:
            # Создаём запись о новом поиске в БД, связывая с текущим пользователем
            search = Searchers.objects.create(
                user=request.user,
                query=query
            )

            # Фильтруем маркетплейсы по выбранным доменам
            marketplaces = Marketplace.objects.filter(
                name__in=marketplace_domains
            )
            # Извлекаем ID маркетплейсов для дальнейшей связи с поиском
            marketplace_ids = marketplaces.values_list('pk', flat=True)

            # Проверяем, что найдены соответствующие маркетплейсы
            if not marketplace_ids:
                # Если маркетплейсы не найдены, перенаправляем обратно
                return redirect('query_list')

            # Связываем поиск с выбранными маркетплейсами через M2M‑связь
            search.marketplaces.set(marketplace_ids)
            # Инициализируем пустой список для сбора ID всех найденных товаров
            all_product_ids = []

            # Перебираем выбранные маркетплейсы для запуска парсинга
            for marketplace in marketplaces:
                if marketplace.name == 'ozon.ru':
                    # Запускаем парсинг на Ozon с передачей запроса и headless‑режима
                    result = ozon_service.scrape_ozon(
                        search_query=query,
                        headless=True
                    )
                    # Добавляем найденные ID товаров из Ozon в общий список
                    all_product_ids.extend(result.get('product_ids', []))
                    print(all_product_ids)  # Отладочный вывод собранных ID
                elif marketplace.name == 'wildberries.ru':
                    print('test1 --wb--')  # Отладочная метка для отслеживания выполнения ветки WB
                    # Запускаем парсинг на Wildberries с передачей запроса и headless‑режима
                    result = wildberries_service.scrape_wb(
                        search_query=query,
                        headless=True
                    )
                    # Добавляем найденные ID товаров из Wildberries в общий список
                    all_product_ids.extend(result.get('product_ids', []))
                    # Отладочные выводы: ID из текущего результата и общий список
                    print(result.get('product_ids', []))
                    print(all_product_ids)
                else:
                    # Пропускаем маркетплейсы, не поддерживаемые текущим сервисом
                    continue

            # Если найдены товары (есть ID), связываем их с записью о поиске
            if all_product_ids:
                search.products.set(
                    Product.objects.filter(product_id__in=all_product_ids)
                )
        except Exception as e:
            # При любой ошибке в процессе парсинга перенаправляем на страницу запросов
            return redirect('query_list')

    # Определяем набор запросов для отображения:
    # - суперпользователь видит все запросы;
    # - обычный пользователь — только свои.
    if request.user.is_superuser:
        searchers = Searchers.objects.all().order_by("-id")  # Все запросы, сортировка по убыванию ID
    else:
        searchers = Searchers.objects.filter(user=request.user).order_by("-id")  # Только запросы текущего пользователя

    # Получаем все доступные маркетплейсы для отображения в форме
    marketplaces = Marketplace.objects.all()

    # Формируем контекст для передачи в шаблон
    context = {
        "marketplaces": marketplaces,  # Список маркетплейсов для выбора в форме
        "searchers": searchers,  # История поисковых запросов (текущего пользователя или всех)
        "current_user": request.user  # Данные текущего пользователя для отображения в интерфейсе
    }

    # Рендерим HTML‑страницу с заполненным контекстом
    return render(
        request,
        "web_scarping/search_list.html",
        context=context,
    )


