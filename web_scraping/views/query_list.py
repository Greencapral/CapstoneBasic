from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from web_scraping.models import Searchers


@login_required
def query_list(request):
    if request.method == 'POST':
        query = request.POST.get('query')
        if query:
            # Создаем запись в базе данных
            Searchers.objects.create(
                user=request.user,
                query=query
            )
            # Здесь можно добавить логику парсинга
            return redirect('query_list')  # Перенаправляем после сохранения
    return render(request, 'web_scarping/search_results.html')