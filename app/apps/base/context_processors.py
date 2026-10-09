from django.conf import settings

from .services import get_services


def platform(request):
    return {
        'platform_name': settings.PLATFORM_NAME,
        'platform_tagline': settings.PLATFORM_TAGLINE,
        'platform_services': get_services(),
    }
