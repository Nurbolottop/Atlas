"""
Сборка промпта для ИИ-разработчика.

Промпт = базовые инструкции стиля + общее дополнение для типа продукта
+ дополнение стиля для этого типа продукта + общие требования.
Все тексты лежат в content/, здесь только порядок и оформление.
"""
from .content import get_common

STATE_LABELS = (
    ('hover', 'Наведение'),
    ('focus', 'Фокус с клавиатуры'),
    ('active', 'Нажатие'),
    ('disabled', 'Отключённое состояние'),
    ('error', 'Ошибка'),
)

COMPONENT_LABELS = (
    ('buttons', 'Кнопки'),
    ('fields', 'Поля ввода'),
    ('cards', 'Карточки'),
    ('navigation', 'Навигация'),
)


def _bullets(items, marker='—'):
    return '\n'.join(f'{marker} {item}' for item in items)


class _Doc:
    def __init__(self):
        self.parts = []
        self.number = 0

    def text(self, value):
        self.parts.append(value.strip())

    def section(self, title, body):
        self.number += 1
        self.parts.append(f'{self.number}. {title.upper()}\n{body.strip()}')

    def render(self):
        return '\n\n'.join(self.parts).strip() + '\n'


def build_prompt(style, product):
    common = get_common()
    p = style['prompt']
    fmt = {
        'style': style['name_ru'],
        'style_en': style['name_en'],
        'product': product['prompt_label'],
    }

    doc = _Doc()
    doc.text(common['title'].format(**fmt))
    doc.text(common['intro'].format(**fmt))
    doc.text(f'ВАЖНО\n{common["scope_notice"]}')

    doc.section('Суть стиля', p['essence'])

    doc.section(
        'Обязательные признаки стиля',
        common['required_intro'] + '\n' + _bullets(p['required']),
    )
    doc.section(
        'Рекомендуемые решения',
        common['recommended_intro'] + '\n' + _bullets(p['recommended']),
    )

    doc.section('Композиция', _bullets(p['composition']))
    doc.section('Визуальная иерархия', _bullets(p['hierarchy']))

    palettes = []
    for palette in style['colors']['palettes']:
        colors = ', '.join(f'{c["hex"]} — {c["role"].lower()}' for c in palette['colors'])
        palettes.append(f'— «{palette["name"]}»: {colors}.')
    doc.section(
        'Цвет',
        _bullets(p['color'])
        + '\n\n' + common['palette_intro'] + '\n' + '\n'.join(palettes),
    )

    pairs = '\n'.join(
        f'— заголовки: {pair["heading"]}, основной текст: {pair["body"]}. {pair["note"]}'
        for pair in style['typography']['pairs']
    )
    doc.section(
        'Типографика',
        _bullets(p['typography'])
        + '\n\n' + common['fonts_intro'] + '\n' + pairs,
    )

    doc.section('Отступы и плотность интерфейса', _bullets(p['spacing']))
    doc.section('Формы, обводки, тени и эффекты', _bullets(p['shapes']))

    components = []
    for key, label in COMPONENT_LABELS:
        components.append(f'{label}:\n' + _bullets(p['components'][key]))
    doc.section('Компоненты', '\n\n'.join(components))

    states = '\n'.join(f'— {label}: {p["states"][key]}' for key, label in STATE_LABELS)
    doc.section('Состояния элементов', states + '\n' + _bullets(common['states_common']))

    doc.section('Анимация', _bullets(p['motion']) + '\n' + _bullets(common['motion_common']))

    doc.section(
        'Читаемость и доступность',
        _bullets(p['accessibility']) + '\n' + _bullets(common['accessibility_common']),
    )

    adaptation = product['prompt']
    doc.section(
        f'Адаптация: {product["prompt_label"]}',
        adaptation['intro']
        + '\n\n' + _bullets(adaptation['rules'])
        + '\n\n' + common['style_product_intro'].format(**fmt)
        + '\n' + _bullets(p['product'][product['slug']])
        + '\n\n' + adaptation['scope'],
    )

    doc.section('Чего избегать', _bullets(p['avoid']))

    doc.section('Итоговая проверка', _bullets(common['checklist']))
    doc.text(common['scope_notice'])
    return doc.render()


def prompt_filename(style, product):
    return f'prompt-{style["slug"]}-{product["slug"]}.txt'
