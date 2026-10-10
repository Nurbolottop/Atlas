"""
Способы использования стиля, которые показываются в разделе «Использовать».

Новый способ = новая запись в USAGE_METHODS и свой маршрут.
Шаблон раздела выводит список как есть.
"""
from dataclasses import dataclass

from django.urls import reverse


@dataclass(frozen=True)
class UsageMethod:
    slug: str
    title: str
    description: str
    action_label: str
    url_name: str

    def url_for(self, style):
        return reverse(self.url_name, args=[style['slug']])


USAGE_METHODS = (
    UsageMethod(
        slug='ai-prompt',
        title='Получить промпт для ИИ',
        description='Инструкция по стилю под ваш тип продукта — для любого ИИ-разработчика.',
        action_label='Выбрать тип продукта',
        url_name='navigator:prompt_type',
    ),
)
