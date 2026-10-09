"""
Загрузка контента «Навигатора дизайна».

Весь текст сервиса хранится в JSON-файлах в `content/`:

    content/taxonomy.json        — типы подходов (направление, приём, компоновка)
    content/product_types.json   — типы продукта и общие дополнения промпта
    content/prompt_common.json   — общие части промпта
    content/showcase.json        — какие демонстрации показать на главной
    content/styles/<slug>.json   — один файл на стиль

Чтобы добавить стиль, достаточно положить новый JSON, шаблоны демонстраций
`templates/navigator/demos/<slug>/{site,app,platform}.html` и стили
`static/navigator/demos/<slug>.css`. Логику страниц менять не нужно.

Структура проверяется функцией `validate()` — она же подключена
к `manage.py check`, поэтому ошибка в контенте видна сразу.
"""
import json
import re
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.template.loader import get_template
from django.template import TemplateDoesNotExist

CONTENT_DIR = Path(__file__).resolve().parent / 'content'
STYLES_DIR = CONTENT_DIR / 'styles'

DEMO_VARIANTS = ('site', 'app', 'platform')

HEX_RE = re.compile(r'^#[0-9A-Fa-f]{6}$')
SLUG_RE = re.compile(r'^[a-z][a-z0-9-]*$')

# Обязательные поля стиля: путь -> ожидаемый тип.
STYLE_SCHEMA = {
    'slug': str,
    'order': int,
    'kind': str,
    'name_ru': str,
    'name_en': str,
    'summary': str,
    'description': list,
    'tags': list,
    'demo_fonts': list,
    'features': list,
    'composition': list,
    'hierarchy': list,
    'colors.principles': list,
    'colors.palettes': list,
    'typography.principles': list,
    'typography.pairs': list,
    'components.buttons': str,
    'components.fields': str,
    'components.cards': str,
    'components.navigation': str,
    'recommendations.fits': list,
    'recommendations.tips': list,
    'limitations': list,
    'mistakes': list,
    'combinations': list,
    'prompt.essence': str,
    'prompt.required': list,
    'prompt.recommended': list,
    'prompt.composition': list,
    'prompt.hierarchy': list,
    'prompt.color': list,
    'prompt.typography': list,
    'prompt.spacing': list,
    'prompt.shapes': list,
    'prompt.components.buttons': list,
    'prompt.components.fields': list,
    'prompt.components.cards': list,
    'prompt.components.navigation': list,
    'prompt.states.hover': str,
    'prompt.states.focus': str,
    'prompt.states.active': str,
    'prompt.states.disabled': str,
    'prompt.states.error': str,
    'prompt.motion': list,
    'prompt.accessibility': list,
    'prompt.avoid': list,
    'prompt.product.site': list,
    'prompt.product.app': list,
    'prompt.product.platform': list,
}


class ContentError(Exception):
    pass


def _read_json(path):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ContentError(f'{path.name}: некорректный JSON — {e}') from e


def _get(data, dotted):
    for key in dotted.split('.'):
        if not isinstance(data, dict) or key not in data:
            return None
        data = data[key]
    return data


def normalize(text):
    """Приводит текст к виду для поиска: нижний регистр, ё → е."""
    return ' '.join(str(text).lower().replace('ё', 'е').split())


class Style(dict):
    """Словарь стиля с удобными свойствами для шаблонов."""

    kind_info = None

    @property
    def search_text(self):
        parts = [self['name_ru'], self['name_en'], self['summary'], *self['description'], *self['tags']]
        return normalize(' '.join(parts))

    def matches(self, query):
        words = normalize(query).split()
        text = self.search_text
        return all(w in text for w in words)

    def demo_template(self, variant):
        return f'navigator/demos/{self["slug"]}/{variant}.html'

    @property
    def demo_css(self):
        return f'navigator/demos/{self["slug"]}.css'


def _load():
    taxonomy = _read_json(CONTENT_DIR / 'taxonomy.json')
    products = _read_json(CONTENT_DIR / 'product_types.json')
    common = _read_json(CONTENT_DIR / 'prompt_common.json')
    showcase = _read_json(CONTENT_DIR / 'showcase.json')

    styles = {}
    for path in sorted(STYLES_DIR.glob('*.json')):
        data = Style(_read_json(path))
        slug = data.get('slug')
        if slug != path.stem:
            raise ContentError(f'{path.name}: slug «{slug}» не совпадает с именем файла')
        data.kind_info = taxonomy.get('kinds', {}).get(data.get('kind'))
        styles[slug] = data

    ordered = dict(sorted(styles.items(), key=lambda kv: (kv[1].get('order', 999), kv[0])))
    return {
        'taxonomy': taxonomy,
        'products': {p['slug']: p for p in products},
        'common': common,
        'showcase': showcase,
        'styles': ordered,
    }


@lru_cache(maxsize=1)
def _cached():
    return _load()


def store():
    # В режиме разработки перечитываем файлы на каждый запрос,
    # чтобы правки текста были видны без перезапуска.
    if settings.DEBUG:
        return _load()
    return _cached()


def get_styles():
    return list(store()['styles'].values())


def get_style(slug):
    return store()['styles'].get(slug)


def get_products():
    return list(store()['products'].values())


def get_product(slug):
    return store()['products'].get(slug)


def get_kind(kind):
    return store()['taxonomy']['kinds'].get(kind)


def get_taxonomy():
    return store()['taxonomy']


def get_common():
    return store()['common']


def get_showcase():
    return store()['showcase']


def font_requests(styles):
    """
    Группы семейств для Google Fonts. У каждого стиля — своя группа из
    `demo_fonts` (начертания разных стилей для одного семейства не конфликтуют),
    плюс общая группа шрифтов из пар типографики, которых нет в `demo_fonts`
    (их показываем только в образцах, базовым начертанием).
    """
    groups, covered = [], set()
    for style in styles:
        specs = style.get('demo_fonts', [])
        if specs and specs not in groups:
            groups.append(specs)
        covered.update(spec.split(':')[0] for spec in specs)
    extra = []
    for style in styles:
        for pair in style.get('typography', {}).get('pairs', []):
            for name in (pair.get('heading'), pair.get('body')):
                if name and name not in covered and name not in extra:
                    extra.append(name)
    if extra:
        groups.append(extra)
    return groups


def validate():
    """
    Проверяет контент. Возвращает (errors, warnings).
    Ошибки ломают страницы; предупреждения — ссылки на ещё не добавленные стили,
    которые страницы просто пропускают.
    """
    errors, warnings = [], []
    try:
        data = _load()
    except (ContentError, OSError) as e:
        return [str(e)], []

    kinds = data['taxonomy'].get('kinds', {})
    slugs = set(data['styles'])

    for product in data['products'].values():
        for key in ('slug', 'title', 'label', 'description', 'prompt_label', 'prompt'):
            if key not in product:
                errors.append(f'product_types.json: у «{product.get("slug")}» нет поля «{key}»')

    if set(data['products']) != set(DEMO_VARIANTS):
        errors.append('product_types.json: типы продукта должны совпадать с ' + ', '.join(DEMO_VARIANTS))

    for slug, style in data['styles'].items():
        prefix = f'styles/{slug}.json'
        if not SLUG_RE.match(slug):
            errors.append(f'{prefix}: недопустимый slug')
        for path, expected in STYLE_SCHEMA.items():
            value = _get(style, path)
            if value is None:
                errors.append(f'{prefix}: нет поля «{path}»')
            elif not isinstance(value, expected):
                errors.append(f'{prefix}: поле «{path}» должно быть {expected.__name__}')
            elif isinstance(value, (str, list)) and not value:
                errors.append(f'{prefix}: поле «{path}» пустое')

        if style.get('kind') not in kinds:
            errors.append(f'{prefix}: неизвестный kind «{style.get("kind")}»')

        for palette in _get(style, 'colors.palettes') or []:
            if not palette.get('name') or not palette.get('colors'):
                errors.append(f'{prefix}: у палитры нет названия или цветов')
            for color in palette.get('colors', []):
                if not HEX_RE.match(color.get('hex', '')):
                    errors.append(f'{prefix}: неверный HEX «{color.get("hex")}» в палитре «{palette.get("name")}»')
                if not color.get('role'):
                    errors.append(f'{prefix}: у цвета {color.get("hex")} не указана роль')

        for pair in _get(style, 'typography.pairs') or []:
            for key in ('heading', 'body', 'note'):
                if not pair.get(key):
                    errors.append(f'{prefix}: в паре шрифтов нет «{key}»')

        for combo in style.get('combinations', []):
            if combo.get('slug') not in slugs:
                warnings.append(f'{prefix}: сочетание ссылается на неизвестный стиль «{combo.get("slug")}»')
            if combo.get('slug') == slug:
                errors.append(f'{prefix}: стиль не может сочетаться сам с собой')
            if not combo.get('note'):
                errors.append(f'{prefix}: у сочетания «{combo.get("slug")}» нет пояснения')

        for variant in DEMO_VARIANTS:
            try:
                get_template(style.demo_template(variant))
            except TemplateDoesNotExist:
                errors.append(f'{prefix}: нет шаблона демонстрации {style.demo_template(variant)}')

        css = Path(settings.BASE_DIR) / 'static' / style.demo_css
        if not css.exists():
            errors.append(f'{prefix}: нет файла стилей демонстрации static/{style.demo_css}')

    for name, items in data['showcase'].items():
        for item in items:
            if item.get('slug') not in slugs:
                warnings.append(f'showcase.json: в подборке «{name}» неизвестный стиль «{item.get("slug")}»')
            if item.get('variant') not in DEMO_VARIANTS:
                errors.append(f'showcase.json: в подборке «{name}» неизвестный вариант «{item.get("variant")}»')

    return errors, warnings
