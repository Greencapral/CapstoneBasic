from celery.result import AsyncResult
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required



@login_required(login_url="login")
def get_progress(request, search_id):
    """
    Получает текущий прогресс выполнения задач парсинга для указанного поиска.
    Проверяет статус Celery‑задач из сессии, рассчитывает средний прогресс
    и возвращает JSON с детальной информацией по каждой задаче и общим статусом.

    Args:
        request (HttpRequest): HTTP‑запрос от клиента.
        search_id (int): идентификатор поиска, для которого запрашивается прогресс.

    Returns:
        JsonResponse: JSON‑ответ с данными о прогрессе выполнения задач:
            - complete (bool): флаг завершения всех задач;
            - progress (int): средний прогресс в процентах;
            - status (str): общий статус процесса;
            - results (list): список объектов с деталями по каждой задаче.
    """
    # Получаем из сессии список ID текущих задач парсинга (пустой список, если нет)
    task_ids = request.session.get('current_tasks', [])
    # Получаем ID поиска из сессии для проверки соответствия
    search_id_session = request.session.get('search_id')

    # Если нет задач или ID поиска не совпадает с сохранённым в сессии, возвращаем завершённый статус
    if not task_ids or search_id != search_id_session:
        return JsonResponse({
            'complete': True,
            'progress': 100,
            'status': 'Нет активных задач',
            'results': []
        })

    # Список для хранения данных по каждой задаче
    results = []
    # Флаг: все ли задачи завершены
    all_complete = True
    # Суммарный прогресс всех задач для расчёта среднего значения
    total_progress = 0

    # Перебираем все задачи из сессии и получаем их статус и прогресс
    for task_id in task_ids:
        # Создаём объект AsyncResult для получения информации о задаче Celery
        task_result = AsyncResult(task_id)

        # Если задача в процессе выполнения (имеет прогресс)
        if task_result.state == 'PROGRESS':
            meta = task_result.info
            progress = meta.get('progress', 0)
            status = meta.get('status', 'В процессе...')
            all_complete = False  # Задача ещё не завершена
        # Если задача успешно завершена
        elif task_result.state == 'SUCCESS':
            meta = task_result.info
            progress = 100
            status = meta.get('status', 'Успешно завершено')
        # Если задача завершилась с ошибкой
        elif task_result.state == 'FAILURE':
            meta = task_result.info
            progress = 0
            status = f"Ошибка: {meta.get('status', 'Неизвестная ошибка')}"
        # Для остальных состояний (PENDING и др.)
        else:
            progress = 0
            status = 'Ожидание...'
            all_complete = False  # Задача ещё не запущена/в ожидании

        # Добавляем данные по текущей задаче в общий список результатов
        results.append({
            'task_id': task_id,
            'state': task_result.state,
            'progress': progress,
            'status': status
        })
        # Накапливаем суммарный прогресс для последующего усреднения
        total_progress += progress

    # Рассчитываем средний прогресс выполнения задач (0, если задач нет)
    avg_progress = total_progress / len(task_ids) if task_ids else 0

    # Определяем общий статус выполнения на основе флага завершения всех задач
    if all_complete:
        status = 'Парсинг полностью завершен'
    else:
        status = 'Парсинг в процессе...'

    # Возвращаем JSON‑ответ с агрегированной информацией о прогрессе
    return JsonResponse({
        'complete': all_complete,
        'progress': round(avg_progress),
        'status': status,
        'results': results
    })
