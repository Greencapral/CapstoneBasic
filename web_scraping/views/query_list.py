from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from web_scraping.models import Searchers,Marketplace,Product
from web_scraping.services import ozon_service, wildberries_service


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
            marketplaces = Marketplace.objects.filter(
                name__in=marketplace_domains
            )
            marketplace_ids = marketplaces.values_list('pk', flat=True)

            if not marketplace_ids:
                return redirect('query_list')

            # search.marketplaces.set(marketplace_ids)
            # return redirect('query_list')

            search.marketplaces.set(marketplace_ids)
            all_product_ids = []  # Список для всех найденных ID

            # Запускаем парсинг на выбранных маркетплейсах
            for marketplace in marketplaces:
                if marketplace.name == 'ozon.ru':
                    result = ozon_service.OzonScrapingService.scrape_ozon(
                        search_query=query,
                        headless=True
                    )
                    all_product_ids.extend(result.get('product_ids', []))
                    print(all_product_ids)
                elif marketplace.name == 'wildberries.ru':
                    print('test1')
                    result = wildberries_service.WildberriesScrapingService.scrape_wildberries(
                        search_query=query,
                        headless=True
                    )
                    all_product_ids.extend(result.get('product_ids', []))
                    print(result.get('product_ids', []))
                    print(all_product_ids)
                else:
                    continue

            # Связываем все найденные товары с поиском
            if all_product_ids:
                search.products.set(
                    Product.objects.filter(product_id__in=all_product_ids)
                )
        except Exception as e:
            # Обработка ошибок
            return redirect('query_list')

    # Фильтрация запросов по пользователю

    if request.user.is_superuser:
        searchers = Searchers.objects.all().order_by("-id")
    else:
        searchers = Searchers.objects.filter(user=request.user).order_by("-id")


    # Получаем все доступные маркетплейсы для формы
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


