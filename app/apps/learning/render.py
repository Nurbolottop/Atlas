"""Превращение Markdown урока в HTML."""
import re
from functools import lru_cache

import markdown
from django.templatetags.static import static
from django.urls import reverse
from markdown.extensions.toc import slugify_unicode

from .content import ASSET_RE, LESSON_RE

EXTENSIONS = ['fenced_code', 'codehilite', 'tables', 'md_in_html', 'sane_lists', 'toc', 'attr_list']
EXTENSION_CONFIGS = {
    'codehilite': {'css_class': 'code', 'guess_lang': False, 'wrapcode': True},
    'toc': {'slugify': slugify_unicode, 'toc_depth': '2-3', 'permalink': False},
}

_EXTERNAL_LINK = re.compile(r'<a href="(https?://[^"]+)"')
_IMAGE = re.compile(r'<img (?![^>]*loading=)')
_TABLE = re.compile(r'<table>(.*?)</table>', re.S)
_CODE = re.compile(r'<div class="code">')


def _toc(tokens):
    items = []
    for token in tokens:
        items.append({'id': token['id'], 'title': token['name'], 'level': token['level']})
        items.extend(_toc(token.get('children', [])))
    return items


@lru_cache(maxsize=256)
def _render(course_slug, source):
    md = markdown.Markdown(extensions=EXTENSIONS, extension_configs=EXTENSION_CONFIGS)
    html = md.convert(source)
    html = ASSET_RE.sub(lambda m: static(f'learning/{course_slug}/{m.group(1)}'), html)
    html = LESSON_RE.sub(lambda m: reverse('learning:lesson', args=[course_slug, m.group(1)]), html)
    html = _EXTERNAL_LINK.sub(r'<a href="\1" target="_blank" rel="noopener"', html)
    html = _IMAGE.sub('<img loading="lazy" decoding="async" ', html)
    html = _TABLE.sub(r'<div class="table-scroll" tabindex="0"><table>\1</table></div>', html)
    html = _CODE.sub('<div class="code" data-code>', html)
    return html, _toc(md.toc_tokens)


def render_lesson(lesson):
    """Возвращает (html, оглавление) урока. Результат кешируется по тексту файла."""
    return _render(lesson.course.slug, lesson.source)
