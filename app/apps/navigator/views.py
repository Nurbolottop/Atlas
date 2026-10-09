from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from .content import DEMO_VARIANTS, get_product, get_products, get_style, get_styles, get_taxonomy
from .prompt import build_prompt, prompt_filename
from .usage import USAGE_METHODS


UNKNOWN_STYLE = 'Такого стиля нет в каталоге. Возможно, адрес набран с ошибкой.'


def _not_found(request):
    return render(request, 'base/404.html', {'message': UNKNOWN_STYLE, 'show_catalog': True}, status=404)


def catalog(request):
    query = request.GET.get('q', '').strip()[:100]
    styles = get_styles()
    matched = [s for s in styles if s.matches(query)] if query else styles
    taxonomy = get_taxonomy()
    return render(request, 'navigator/catalog.html', {
        'styles': styles,
        'matched_slugs': {s['slug'] for s in matched},
        'matched_count': len(matched),
        'query': query,
        'kinds': taxonomy['kinds'],
        'kinds_note': taxonomy['note'],
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
