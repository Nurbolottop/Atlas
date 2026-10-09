from django.core.checks import Error, Warning, register

from .content import validate


@register()
def navigator_content_check(app_configs, **kwargs):
    errors, warnings = validate()
    hint = 'Исправьте файл в apps/navigator/content/'
    return [
        *(Error(message, id='navigator.E001', hint=hint) for message in errors),
        *(Warning(message, id='navigator.W001', hint=hint) for message in warnings),
    ]
