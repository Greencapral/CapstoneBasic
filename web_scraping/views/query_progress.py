import time
from django.shortcuts import render
from django.contrib.auth.decorators import login_required



@login_required(login_url="login")
def query_progress(request, search_id):
    """
    Отображает страницу прогресса выполнения задач парсинга для указанного поиска.
    Сохраняет в сессии время начала выполнения задач и ID поиска, затем рендерит
    шаблон страницы прогресса.

    Args:
        request (HttpRequest): HTTP‑запрос от клиента.
        search_id (int): идентификатор поиска, для которого отображается прогресс.

    Returns:
        HttpResponse: рендер страницы прогресса выполнения задач.
    """
    # Сохраняем текущее время в сессии как время начала выполнения задач
    request.session['task_start_time'] = time.time()
    # Сохраняем ID поиска в сессии для дальнейшего использования
    request.session['search_id'] = search_id

    # Формируем контекст для передачи в шаблон
    context = {
        'search_id': search_id,           # ID поиска для отображения прогресса
        'current_user': request.user     # Текущий авторизованный пользователь
    }

    # Рендерим шаблон страницы прогресса с переданным контекстом
    return render(
        request,
        "web_scarping/progress.html",
        context=context
    )
