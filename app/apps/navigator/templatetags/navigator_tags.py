from django import template
from django.urls import reverse
from django.utils.html import format_html

from ..assets import css_bundle, font_urls
from ..content import get_showcase, get_style, get_styles

register = template.Library()

# Размер «виртуального холста» демонстрации. Демонстрация верстается
# в этих пикселях и масштабируется под контейнер (static/platform/app.js).
CANVAS = {
    'site': (1200, 800),
    'app': (390, 800),
    'platform': (1280, 800),
}


@register.inclusion_tag('navigator/includes/demo_stage.html')
def demo_stage(style, variant, preview=False, label=''):
    width, height = CANVAS[variant]
    return {
        'style': style,
        'variant': variant,
        'template': style.demo_template(variant),
        'width': width,
        'height': height,
        'preview': preview,
        'label': label,
    }


@register.simple_tag
def demo_assets(*styles, pairs=None):
    """
    Подключает ассеты демонстраций: единый CSS всех демо и шрифты нужных стилей.
    `pairs` — стиль, для которого нужны ещё и шрифты образцов типографики.
    Шрифты грузятся без блокировки отрисовки.
    """
    flat = []
    for item in styles:
        flat.extend(item if isinstance(item, (list, tuple)) else [item])

    version, _ = css_bundle(get_styles())
    tags = [format_html(
        '<link rel="stylesheet" href="{}?v={}">', reverse('navigator:demo_bundle'), version
    )]
    for url in font_urls(flat, [pairs] if pairs else []):
        tags.append(format_html(
            '<link rel="preload" as="style" href="{0}" onload="this.onload=null;this.rel=\'stylesheet\'">'
            '<noscript><link rel="stylesheet" href="{0}"></noscript>', url
        ))
    return format_html(''.join(['{}'] * len(tags)), *tags)


@register.simple_tag
def showcase(name):
    """Подборка демонстраций для главной из content/showcase.json."""
    entries = []
    for item in get_showcase().get(name, []):
        style = get_style(item['slug'])
        if style:
            entries.append({**item, 'style': style})
    return {'entries': entries, 'styles': [e['style'] for e in entries]}


@register.filter
def ru_plural(number, forms):
    """{{ n|ru_plural:"стиль,стиля,стилей" }}"""
    one, few, many = forms.split(',')
    n = abs(int(number))
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many
