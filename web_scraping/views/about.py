from django.shortcuts import render


def about(request):
    return render(request, "web_scarping/about_page.html")
