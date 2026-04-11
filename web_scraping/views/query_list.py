import time
from celery.result import AsyncResult
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
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


@login_required(login_url="login")
def get_progress(request, search_id):
    """API endpoint для получения прогресса парсинга."""
    task_ids = request.session.get('current_tasks', [])
    search_id_session = request.session.get('search_id')

    if not task_ids or search_id != search_id_session:
        return JsonResponse({
            'complete': True,
            'progress': 100,
            'status': 'Нет активных задач',
            'results': []
        })

    results = []
    all_complete = True
    total_progress = 0

    for task_id in task_ids:
        task_result = AsyncResult(task_id)

        if task_result.state == 'PROGRESS':
            meta = task_result.info
            progress = meta.get('progress', 0)
            status = meta.get('status', 'В процессе...')
            all_complete = False
        elif task_result.state == 'SUCCESS':
            meta = task_result.info
            progress = 100
            status = meta.get('status', 'Успешно завершено')
        elif task_result.state == 'FAILURE':
            meta = task_result.info
            progress = 0
            status = f"Ошибка: {meta.get('status', 'Неизвестная ошибка')}"
        else:
            progress = 0
            status = 'Ожидание...'
            all_complete = False

        results.append({
            'task_id': task_id,
            'state': task_result.state,
            'progress': progress,
            'status': status
        })
        total_progress += progress

    avg_progress = total_progress // len(task_ids) if task_ids else 0

    # Если прошло 20 секунд, принудительно завершаем ожидание
    start_time = request.session.get('task_start_time', time.time())
    elapsed = time.time() - start_time

    if elapsed >= 20:
        all_complete = True
        status = "Таймаут 20 секунд достигнут. Показываем результаты."

    return JsonResponse({
        'complete': all_complete,
        'progress': avg_progress,
        'status': status,
        'results': results
    })

def query_progress(request, search_id):
    """Страница отображения прогресса парсинга."""
    # Сохраняем время начала задач
    request.session['task_start_time'] = time.time()

    context = {
        'search_id': search_id,
        'current_user': request.user
    }
    return render(request, "web_scarping/progress.html", context)
