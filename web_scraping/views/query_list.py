from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from web_scraping.models import Marketplace, Searchers
from web_scraping.tasks import scrape_marketplace_task

@login_required(login_url="login")
def query_list(request):
    if request.method == 'POST':
        query = request.POST.get('query')
        marketplace_domains = request.POST.getlist('marketplaces[]')

        if not query:
            return redirect('query_list')

        try:
            # Создаём запись о поиске
            search = Searchers.objects.create(
                user=request.user,
                query=query
            )

            # Получаем выбранные маркетплейсы
            marketplaces = Marketplace.objects.filter(
                name__in=marketplace_domains
            )
            marketplace_ids = marketplaces.values_list('pk', flat=True)

            if not marketplace_ids:
                return redirect('query_list')

            search.marketplaces.set(marketplace_ids)

            # Запускаем задачи парсинга параллельно
            task_ids = []
            for marketplace in marketplaces:
                task = scrape_marketplace_task.delay(
                    marketplace_name=marketplace.name,
                    query=query,
                    search_id=search.pk
                )
                task_ids.append(task.id)

            # Сохраняем ID задач в сессии для отслеживания прогресса
            request.session['current_tasks'] = task_ids
            request.session['search_id'] = search.pk

            # Перенаправляем на страницу с прогрессом            
            return redirect('query_progress', search_id=search.pk)

        except Exception as e:
            print(f"Ошибка создания поиска: {e}")
            return redirect('query_list')

    # Остальная часть вьюшки для GET‑запроса
    if request.user.is_superuser:
        searchers = Searchers.objects.all().order_by("-id")
    else:
        searchers = Searchers.objects.filter(user=request.user).order_by("-id")

    marketplaces = Marketplace.objects.all()

    context = {
        "marketplaces": marketplaces,
        "searchers": searchers,
        "current_user": request.user
    }

    return render(
        request,
        "web_scarping/search_list.html",
        context=context,
    )

