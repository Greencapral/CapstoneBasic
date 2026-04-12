import time
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required(login_url="login")
def query_progress(request, search_id):
    # Сохраняем время начала задач
    request.session['task_start_time'] = time.time()
    request.session['search_id'] = search_id

    context = {
        'search_id': search_id,
        'current_user': request.user
    }
    return render(request, "web_scarping/progress.html", context)