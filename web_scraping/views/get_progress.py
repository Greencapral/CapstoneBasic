from celery.result import AsyncResult
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required(login_url="login")
def get_progress(request, search_id):
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

    # Вычисляем средний прогресс
    avg_progress = total_progress / len(task_ids) if task_ids else 0

    # Проверяем, все ли задачи завершены
    if all_complete:
        status = 'Парсинг полностью завершен'
    else:
        status = 'Парсинг в процессе...'

    return JsonResponse({
        'complete': all_complete,
        'progress': round(avg_progress),
        'status': status,
        'results': results
    })
