from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from web_scraping.models import Marketplace, Searchers
from web_scraping.tasks import scrape_marketplace_task



@login_required(login_url="login")
def query_list(request):
    """
    Отображает список поисковых запросов и обрабатывает новые запросы на парсинг маркетплейсов.
    При POST‑запросе создаёт запись поиска, запускает задачи парсинга для выбранных маркетплейсов
    и перенаправляет на страницу прогресса. При GET‑запросе отображает список запросов
    (для суперпользователя — все, для обычного пользователя — только его).

    Args:
        request (HttpRequest): HTTP‑запрос от клиента.

    Returns:
        HttpResponse: рендер страницы или перенаправление на другую страницу.
    """
    if request.method == 'POST':
        # Получаем поисковый запрос из данных формы
        query = request.POST.get('query')
        # Получаем список выбранных маркетплейсов из данных формы
        marketplace_domains = request.POST.getlist('marketplaces[]')

        # Если запрос пуст, перенаправляем обратно на ту же страницу
        if not query:
            return redirect('query_list')

        try:
            # Создаём новую запись поискового запроса в БД, связывая её с текущим пользователем
            search = Searchers.objects.create(
                user=request.user,
                query=query
            )

            # Фильтруем маркетплейсы по выбранным доменам
            marketplaces = Marketplace.objects.filter(
                name__in=marketplace_domains
            )
            # Извлекаем ID маркетплейсов для связи с поиском
            marketplace_ids = marketplaces.values_list('pk', flat=True)

            # Если ни один маркетплейс не выбран, перенаправляем обратно
            if not marketplace_ids:
                return redirect('query_list')

            # Связываем поисковый запрос с выбранными маркетплейсами
            search.marketplaces.set(marketplace_ids)

            # Список для хранения ID запущенных задач Celery
            task_ids = []
            for marketplace in marketplaces:
                # Запускаем асинхронную задачу парсинга для каждого маркетплейса
                task = scrape_marketplace_task.delay(
                    marketplace_name=marketplace.name,
                    query=query,
                    search_id=search.pk
                )
                # Сохраняем ID задачи для отслеживания прогресса
                task_ids.append(task.id)

            # Сохраняем ID задач и ID поиска в сессии пользователя
            request.session['current_tasks'] = task_ids
            request.session['search_id'] = search.pk

            # Перенаправляем на страницу прогресса с ID поиска
            return redirect('query_progress', search_id=search.pk)

        except Exception as e:
            # Логируем ошибку создания поиска
            print(f"Ошибка создания поиска: {e}")
            # При ошибке перенаправляем обратно на страницу списка запросов
            return redirect('query_list')

    # Для GET‑запроса определяем набор запросов для отображения
    if request.user.is_superuser:
        # Суперпользователь видит все запросы, отсортированные по убыванию ID
        searchers = Searchers.objects.all().order_by("-id")
    else:
        # Обычный пользователь видит только свои запросы, отсортированные по убыванию ID
        searchers = Searchers.objects.filter(user=request.user).order_by("-id")

    # Получаем все доступные маркетплейсы для отображения в форме
    marketplaces = Marketplace.objects.all()

    # Формируем контекст для передачи в шаблон
    context = {
        "marketplaces": marketplaces,  # Список маркетплейсов
        "searchers": searchers,      # Список поисковых запросов
        "current_user": request.user  # Текущий пользователь
    }

    # Рендерим шаблон страницы списка запросов с переданным контекстом
    return render(
        request,
        "web_scarping/search_list.html",
        context=context,
    )
