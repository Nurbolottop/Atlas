"""
Ассеты демонстраций: шрифты Google Fonts и единая связка CSS.

Вместо отдельного <link> на каждый стиль страница получает:
— один файл со стилями всех демонстраций (кешируется браузером надолго,
  версия в адресе меняется при изменении любого CSS);
— несколько объединённых запросов к Google Fonts, где начертания одного
  семейства из разных стилей сливаются в один набор.
"""
import hashlib
from pathlib import Path
from urllib.parse import quote

from django.conf import settings

FONTS_PER_REQUEST = 8


def _parse(spec):
    """'Family:ital,wght@0,400;1,400' -> ('Family', {(0, 400), (1, 400)}); 'Family' -> ('Family', None)."""
    if ':' not in spec:
        return spec, None
    family, axes = spec.split(':', 1)
    names, values = axes.split('@', 1)
    names = names.split(',')
    result = set()
    for chunk in values.split(';'):
        parts = dict(zip(names, (int(v) for v in chunk.split(','))))
        result.add((parts.get('ital', 0), parts.get('wght', 400)))
    return family, result


def _format(family, variants):
    name = family.replace(' ', '+')
    if variants is None:
        return name
    if any(ital for ital, _ in variants):
        values = ';'.join(f'{i},{w}' for i, w in sorted(variants))
        return f'{name}:ital,wght@{values}'
    return f'{name}:wght@' + ';'.join(str(w) for _, w in sorted(variants))


def font_urls(styles, pair_styles=()):
    """
    Адреса Google Fonts для демонстраций `styles` и образцов шрифтовых пар
    `pair_styles` (пары нужны только на странице самого стиля).
    """
    families = {}
    for style in styles:
        for spec in style.get('demo_fonts', []):
            family, variants = _parse(spec)
            if variants is None:
                families.setdefault(family, None)
            elif families.get(family) is None:
                families[family] = set(variants)
            else:
                families[family] |= variants
    for style in pair_styles:
        for pair in style.get('typography', {}).get('pairs', []):
            for name in (pair.get('heading'), pair.get('body')):
                if name:
                    families.setdefault(name, None)

    specs = [_format(f, v) for f, v in families.items()]
    urls = []
    for i in range(0, len(specs), FONTS_PER_REQUEST):
        query = '&'.join('family=' + quote(s, safe=':;@,+') for s in specs[i:i + FONTS_PER_REQUEST])
        urls.append(f'https://fonts.googleapis.com/css2?{query}&display=swap')
    return urls


def _css_files(styles):
    root = Path(settings.BASE_DIR) / 'static'
    return [root / s.demo_css for s in styles if (root / s.demo_css).exists()]


_bundle_cache = {}


def css_bundle(styles):
    """(версия, текст) единого CSS для всех переданных стилей."""
    files = _css_files(styles)
    key = tuple((str(f), f.stat().st_mtime_ns, f.stat().st_size) for f in files)
    if key not in _bundle_cache:
        text = '\n'.join(f'/* {f.name} */\n' + f.read_text(encoding='utf-8') for f in files)
        version = hashlib.sha1(text.encode('utf-8')).hexdigest()[:12]
        _bundle_cache.clear()
        _bundle_cache[key] = (version, text)
    return _bundle_cache[key]
