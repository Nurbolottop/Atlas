from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from .assets import css_bundle
from .content import DEMO_VARIANTS, get_product, get_products, get_style, get_styles, get_taxonomy
from .prompt import build_prompt, prompt_filename
from .usage import USAGE_METHODS


UNKNOWN_STYLE = 'Такого стиля нет в каталоге. Возможно, адрес набран с ошибкой.'


def _not_found(request):
    return render(request, 'base/404.html', {'message': UNKNOWN_STYLE, 'show_catalog': True}, status=404)


def catalog(request):
    query = request.GET.get('q', '').strip()[:100]
    styles = get_styles()
    taxonomy = get_taxonomy()
    kind = request.GET.get('kind', '')
    if kind not in taxonomy['kinds']:
        kind = ''
    matched = [s for s in styles if (not query or s.matches(query)) and (not kind or s['kind'] == kind)]

    kind_filters = [{'key': '', 'label': 'Все', 'count': len(styles), 'description': ''}]
    for key, info in taxonomy['kinds'].items():
        kind_filters.append({
            'key': key, 'label': info['plural'], 'description': info['description'],
            'count': sum(1 for s in styles if s['kind'] == key),
        })

    fonts = {spec.split(':')[0] for s in styles for spec in s['demo_fonts']}
    fonts |= {name for s in styles for p in s['typography']['pairs'] for name in (p['heading'], p['body'])}
    stats = [
        {'value': len(styles), 'forms': 'стиль,стиля,стилей'},
        {'value': len(styles) * len(DEMO_VARIANTS), 'forms': 'демо,демо,демо'},
        {'value': len(fonts), 'forms': 'шрифт с кириллицей,шрифта с кириллицей,шрифтов с кириллицей'},
        {'value': len(get_products()), 'forms': 'тип продукта,типа продукта,типов продукта'},
    ]
    return render(request, 'navigator/catalog.html', {
        'styles': styles,
        'matched_slugs': {s['slug'] for s in matched},
        'matched_count': len(matched),
        'query': query,
        'kind': kind,
        'kind_filters': kind_filters,
        'kinds_note': taxonomy['note'],
        'stats': stats,
    })


def style_detail(request, slug):
    style = get_style(slug)
    if style is None:
        return _not_found(request)

    demo = request.GET.get('demo')
    if demo not in DEMO_VARIANTS:
        demo = DEMO_VARIANTS[0]

    combinations = []
    for combo in style['combinations']:
        other = get_style(combo['slug'])
        if other:
            combinations.append({'style': other, 'note': combo['note']})

    return render(request, 'navigator/style.html', {
        'style': style,
        'kinds_note': get_taxonomy()['note'],
        'products': get_products(),
        'active_demo': demo,
        'combinations': combinations,
        'combinations_styles': [c['style'] for c in combinations],
    })


def style_use(request, slug):
    style = get_style(slug)
    if style is None:
        return _not_found(request)
    methods = [{'method': m, 'url': m.url_for(style)} for m in USAGE_METHODS]
    return render(request, 'navigator/use.html', {'style': style, 'methods': methods})


def prompt_type(request, slug):
    style = get_style(slug)
    if style is None:
        return _not_found(request)

    error = None
    if 'product' in request.GET:
        product = get_product(request.GET['product'])
        if product:
            return redirect('navigator:prompt_result', slug=slug, product=product['slug'])
        error = 'Выберите тип продукта, чтобы получить промпт.'

    selected = request.GET.get('current')
    if not get_product(selected or ''):
        selected = None

    return render(request, 'navigator/prompt_type.html', {
        'style': style,
        'products': get_products(),
        'selected': selected,
        'error': error,
    }, status=400 if error else 200)


def prompt_result(request, slug, product):
    style = get_style(slug)
    if style is None:
        return _not_found(request)
    product_data = get_product(product)
    if product_data is None:
        return redirect(reverse('navigator:prompt_type', args=[slug]))

    return render(request, 'navigator/prompt_result.html', {
        'style': style,
        'product': product_data,
        'prompt': build_prompt(style, product_data),
        'filename': prompt_filename(style, product_data),
    })


def prompt_download(request, slug, product):
    style = get_style(slug)
    product_data = get_product(product)
    if style is None or product_data is None:
        return _not_found(request)
    response = HttpResponse(build_prompt(style, product_data), content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{prompt_filename(style, product_data)}"'
    return response


def demo_bundle(request):
    version, text = css_bundle(get_styles())
    response = HttpResponse(text, content_type='text/css; charset=utf-8')
    if request.GET.get('v') == version:
        response['Cache-Control'] = 'public, max-age=31536000, immutable'
    else:
        response['Cache-Control'] = 'no-cache'
    response['ETag'] = f'"{version}"'
    return response
