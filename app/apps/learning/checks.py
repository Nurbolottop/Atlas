from django.core.checks import Error, Warning, register

from .content import validate


@register()
def learning_content_check(app_configs, **kwargs):
    errors, warnings = validate()
    hint = 'Исправьте файлы в apps/learning/content/'
    return [
        *(Error(message, id='learning.E001', hint=hint) for message in errors),
        *(Warning(message, id='learning.W001', hint=hint) for message in warnings),
    ]
