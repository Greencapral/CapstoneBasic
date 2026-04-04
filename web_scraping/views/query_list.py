from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from web_scraping.models import Searchers,Marketplace,Product


@login_required(login_url="login")
def query_list(request):
    if request.method == 'POST':
        query = request.POST.get('query')
        marketplace_domains = request.POST.getlist('marketplaces[]')

        if not query:
            return redirect('query_list')

        try:
            # Создаем запись поиска
            search = Searchers.objects.create(
                user=request.user,
                query=query
            )

            # Получаем ID маркетплейсов
            marketplace_ids = Marketplace.objects.filter(
                domain__in=marketplace_domains
            ).values_list('id', flat=True)

            if not marketplace_ids:
                # Если маркетплейсы не найдены
                return redirect('query_list')

            search.marketplaces.set(marketplace_ids)
            return redirect('query_list')

        except Exception as e:
            # Обработка ошибок
            return redirect('query_list')

    # Получаем все доступные маркетплейсы для формы
    marketplaces = Marketplace.objects.all()
    searchers = Searchers.objects.all().order_by("-id")
    context = {
        "marketplaces": marketplaces,
        "searchers": searchers,
    }
    return render(
        request,
        "web_scarping/search_list.html",
        context=context,
    )


