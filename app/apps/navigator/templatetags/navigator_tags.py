from urllib.parse import quote

from django import template
from django.templatetags.static import static
from django.utils.html import format_html

from ..content import font_requests, get_showcase, get_style

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
def demo_assets(*styles):
    """<link> на шрифты и CSS демонстраций для переданных стилей."""
    flat = []
    for item in styles:
        flat.extend(item if isinstance(item, (list, tuple)) else [item])

    tags = []
    for families in font_requests(flat):
        query = '&'.join('family=' + quote(f.replace(' ', '+'), safe=':;@,+') for f in families)
        tags.append(format_html(
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{}&display=swap">', query
        ))
    for style in flat:
        tags.append(format_html('<link rel="stylesheet" href="{}">', static(style.demo_css)))
    return format_html(''.join(['{}'] * len(tags)), *tags) if tags else ''


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
