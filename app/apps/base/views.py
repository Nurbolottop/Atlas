from django.shortcuts import render

from .services import get_hero_service


def home(request):
    return render(request, 'base/home.html', {'hero_service': get_hero_service()})


def page_not_found(request, exception=None):
    return render(request, 'base/404.html', status=404)
