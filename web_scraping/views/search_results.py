from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from web_scraping.models import Product, Marketplace

def search_results(request):
    query = request.GET.get('query', '').strip()
    marketplaces = request.GET.getlist('marketplaces[]')

    # Получаем все площадки для отображения в фильтре
    all_marketplaces = Marketplace.objects.all()

    marketplace_ids = []
    for marketplace_name in marketplaces:
        try:
            marketplace = Marketplace.objects.get(name=marketplace_name)
            marketplace_ids.append(marketplace.pk)
        except ObjectDoesNotExist:
            pass

    print("Request method:", request.method)
    print("Full GET data:", request.GET)
    print("Query:", query)
    print("Marketplaces_ids:", marketplaces)

    products = Product.objects.filter(name__icontains=query)

    if marketplace_ids:
        products = products.filter(marketplace__in=marketplace_ids)

    print("Products:", products.count())

    context = {
        'products': products,
        'query': query,
        'all_marketplaces': all_marketplaces,
        'selected_marketplaces': marketplaces,  # Для отметки выбранных площадок
    }

    return render(request, 'web_scarping/search_results.html', context=context)
