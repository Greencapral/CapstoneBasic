from django.shortcuts import render
from web_scraping.models import Product

def search_results(request):

    query = request.GET.get('query','')
    platforms = request.GET.getlist('platforms')
    print("Query:", request.GET.get('query'))
    print("Platforms:", request.GET.getlist('platforms'))

    products = Product.objects.filter(
        name__icontains=query
    )
    if platforms:
        products = products.filter(platform__in=platforms)

    context = {
        'products': products,
        'query': query,
    }

    return render(request, 'web_scarping/search_results.html', context=context)
