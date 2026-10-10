"""
Перенос курса из публичной страницы Notion в файлы `content/`.

Notion отдаёт опубликованные страницы через свой внутренний API
(`<site>.notion.site/api/v3/...`), без ключей. Мы обходим дерево страниц,
превращаем блоки в Markdown и скачиваем картинки и файлы к себе: ссылки
Notion на вложения со временем перестают работать.

Структура курса строится так:
    страница курса → разделы (страницы первого уровня) → уроки.
Страницы третьего уровня становятся уроками того же раздела сразу после
родителя; пустые страницы-группы пропускаются.

Используется командой `manage.py import_notion`.
"""
import json
import mimetypes
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

from .text import slugify

CODE_LANGUAGES = {
    'plain text': 'text', 'shell': 'bash', 'c++': 'cpp', 'c#': 'csharp',
    'markup': 'html', 'docker': 'docker', 'f#': 'fsharp',
}

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'

HEADINGS = {'header': '##', 'sub_header': '###', 'sub_sub_header': '####'}


class NotionError(Exception):
    pass


class NotionClient:
    def __init__(self, site, retries=4):
        self.site = site.rstrip('/')
        self.retries = retries

    def _request(self, url, data=None, headers=None):
        error = None
        for attempt in range(self.retries):
            try:
                request = urllib.request.Request(url, data=data, headers={'user-agent': USER_AGENT, **(headers or {})})
                with urllib.request.urlopen(request, timeout=60) as response:
                    return response.read(), response.headers.get('content-type', '')
            except Exception as e:  # сеть или 5xx — пробуем ещё раз
                error = e
                time.sleep(2 * (attempt + 1))
        raise NotionError(f'{url}: {error}')

    def api(self, endpoint, body):
        raw, _ = self._request(
            f'{self.site}/api/v3/{endpoint}', json.dumps(body).encode(), {'content-type': 'application/json'},
        )
        return json.loads(raw)

    def download(self, source, block_id):
        """Скачивает вложение блока. Возвращает (bytes, content-type)."""
        if not ('secure.notion-static.com' in source or 'prod-files-secure' in source or source.startswith('attachment:')):
            try:
                return self._request(source)
            except NotionError:
                # Внешний сайт мог закрыться — берём копию из веб-архива.
                return self._request(f'https://web.archive.org/web/2020id_/{source}')
        try:
            return self._request(f'{self.site}/image/{urllib.parse.quote(source, safe="")}?table=block&id={block_id}')
        except NotionError:
            # Не картинки (PDF и т.п.) прокси не отдаёт — просим подписанную ссылку.
            data = self.api('getSignedFileUrls', {
                'urls': [{'url': source, 'permissionRecord': {'table': 'block', 'id': block_id}}],
            })
            urls = data.get('signedUrls') or []
            if not urls:
                raise
            return self._request(urls[0])


def _value(record):
    value = record.get('value', {})
    return value.get('value', value)


@dataclass
class Page:
    id: str
    title: str
    icon: str
    depth: int
    blocks: list  # id дочерних блоков
    children: list = field(default_factory=list)  # дочерние страницы
    slug: str = ''

    @property
    def has_content(self):
        return bool(self.blocks)


class NotionCourse:
    """Загруженное дерево страниц курса со всеми блоками и таблицами."""

    def __init__(self, client, root_id, log=print):
        self.client = client
        self.root_id = root_id
        self.log = log
        self.blocks = {}
        self.collections = {}  # id блока таблицы -> {'columns': [...], 'rows': [[...]]}

    # ---------- загрузка ----------

    def _store(self, record_map):
        for key, record in record_map.get('block', {}).items():
            value = _value(record)
            if value:
                self.blocks[key] = value

    def _load_page(self, page_id):
        cursor, chunk = {'stack': []}, 0
        while True:
            data = self.client.api('loadCachedPageChunk', {
                'page': {'id': page_id}, 'limit': 100, 'cursor': cursor,
                'chunkNumber': chunk, 'verticalColumns': False,
            })
            self._store(data.get('recordMap', {}))
            cursor = data.get('cursor') or {}
            if not cursor.get('stack'):
                return
            chunk += 1

    def _load_missing(self, ids):
        ids = [i for i in ids if i not in self.blocks]
        for start in range(0, len(ids), 100):
            data = self.client.api('syncRecordValuesMain', {
                'requests': [{'pointer': {'table': 'block', 'id': i}, 'version': -1} for i in ids[start:start + 100]],
            })
            self._store(data.get('recordMap', {}))

    def _load_collection(self, block):
        collection_id = block.get('collection_id') or block.get('format', {}).get('collection_pointer', {}).get('id')
        view_id = (block.get('view_ids') or [None])[0]
        if not collection_id or not view_id:
            return
        data = self.client.api('queryCollection', {
            'collection': {'id': collection_id},
            'collectionView': {'id': view_id},
            'source': {'type': 'collection', 'id': collection_id},
            'loader': {
                'type': 'reducer', 'searchQuery': '', 'userTimeZone': 'UTC',
                'reducers': {'collection_group_results': {'type': 'results', 'limit': 500}},
            },
        })
        record_map = data.get('recordMap', {})
        collection = _value(record_map.get('collection', {}).get(collection_id, {}))
        view = _value(record_map.get('collection_view', {}).get(view_id, {}))
        schema = collection.get('schema', {})
        order = [p['property'] for p in view.get('format', {}).get('table_properties', []) if p.get('visible', True)]
        order = [p for p in order if p in schema] or (['title'] + [p for p in schema if p != 'title'])
        row_ids = data.get('result', {}).get('reducerResults', {}).get('collection_group_results', {}).get('blockIds', [])
        rows = []
        for row_id in row_ids:
            row = _value(record_map.get('block', {}).get(row_id, {}))
            if row:
                rows.append(row)
        self.collections[block['id']] = {
            'name': clean_title(rich_plain(collection.get('name'))),
            'columns': [schema[p]['name'] for p in order],
            'types': [schema[p]['type'] for p in order],
            'rows': [[row.get('properties', {}).get(p) for p in order] for row in rows],
        }

    def load(self):
        seen, queue = set(), [self.root_id]
        while queue:
            page_id = queue.pop(0)
            if page_id in seen:
                continue
            seen.add(page_id)
            self._load_page(page_id)
            stack = [page_id]
            while stack:
                block = self.blocks.get(stack.pop())
                if not block:
                    continue
                content = block.get('content') or []
                self._load_missing(content)
                for child_id in content:
                    child = self.blocks.get(child_id)
                    if not child:
                        continue
                    if child['type'] == 'page':
                        queue.append(child_id)
                    elif child['type'] in ('collection_view', 'collection_view_page'):
                        self._load_collection(child)
                    else:
                        stack.append(child_id)
            self.log(f'  загружено страниц: {len(seen)}')

    # ---------- дерево ----------

    def page(self, page_id, depth=0):
        block = self.blocks[page_id]
        own, children = [], []
        for child_id in block.get('content') or []:
            child = self.blocks.get(child_id)
            if not child:
                continue
            if child['type'] == 'page':
                children.append(self.page(child_id, depth + 1))
            elif _is_meaningful(child):
                own.append(child_id)
        icon = block.get('format', {}).get('page_icon', '')
        return Page(
            id=page_id, title=clean_title(rich_plain(block.get('properties', {}).get('title'))),
            icon=icon if icon and not icon.startswith('http') else '', depth=depth, blocks=own, children=children,
        )


def _is_meaningful(block):
    if block['type'] == 'text':
        return bool(rich_plain(block.get('properties', {}).get('title')).strip()) or bool(block.get('content'))
    return block['type'] != 'divider'


def clean_title(title):
    title = re.sub(r'^Copy of\s+', '', title.strip())
    return re.sub(r'\s+', ' ', title)


# ---------- текст ----------

def rich_plain(rich):
    return ''.join(part[0] for part in rich or [] if part and isinstance(part[0], str))


_ESCAPE = re.compile(r'([\\`*_\[\]])')
_LINE_START = re.compile(r'^(\s*)(#|>|[-+*](?=\s)|\d+\.(?=\s))', re.M)


def escape(text):
    text = _ESCAPE.sub(r'\\\1', text).replace('<', '&lt;')
    return _LINE_START.sub(lambda m: m.group(1) + '\\' + m.group(2), text)


def _wrap(text, left, right=None):
    """Оборачивает текст в разметку, оставляя пробелы по краям снаружи."""
    stripped = text.strip()
    if not stripped:
        return text
    start = text[:len(text) - len(text.lstrip())]
    end = text[len(text.rstrip()):]
    return f'{start}{left}{stripped}{right if right is not None else left}{end}'


def _code_span(text):
    ticks = '``' if '`' in text else '`'
    pad = ' ' if ticks == '``' else ''
    return f'{ticks}{pad}{text}{pad}{ticks}'


class InlineRenderer:
    def __init__(self, link_for_page):
        self.link_for_page = link_for_page

    def __call__(self, rich):
        # Соседние куски с одинаковым оформлением склеиваем: иначе получится «**а****б**».
        merged = []
        for part in rich or []:
            if not part:
                continue
            text = part[0]
            marks = part[1] if len(part) > 1 else []
            key = json.dumps(sorted(marks, key=lambda m: json.dumps(m)))
            if merged and merged[-1][1] == key and text != '‣':
                merged[-1][0] += text
            else:
                merged.append([text, key, marks])
        return ''.join(self._segment(text, marks) for text, _, marks in merged)

    def _segment(self, text, marks):
        names = {m[0]: (m[1] if len(m) > 1 else None) for m in marks}
        if 'p' in names:  # упоминание страницы
            title, url = self.link_for_page(names['p'])
            return f'[{escape(title)}]({url})' if url else escape(title)
        if 'e' in names:  # формула
            return _code_span(names['e'] or text)
        if 'd' in names or 'u' in names:
            return ''
        if 'c' in names:
            out = _code_span(text)
        else:
            out = escape(text)
        if 's' in names:
            out = _wrap(out, '~~')
        if 'i' in names:
            out = _wrap(out, '*')
        if 'b' in names:
            out = _wrap(out, '**')
        if 'a' in names and names['a']:
            href = names['a']
            target = _notion_page_id(href)
            if target:
                _, url = self.link_for_page(target)
                href = url or href
            if out.strip() and _SAFE_HREF.match(href):
                out = f'[{out}]({href.replace(" ", "%20").replace(")", "%29")})'
        return out


# Ссылки из Notion попадают в HTML урока как есть: javascript: и прочие схемы не пускаем.
_SAFE_HREF = re.compile(r'^(https?://|mailto:|lesson:|/|#)', re.I)

_NOTION_ID = re.compile(r'([0-9a-f]{32})(?:[?#].*)?$')


def _notion_page_id(href):
    if 'notion.so' not in href and 'notion.site' not in href and not href.startswith('/'):
        return None
    match = _NOTION_ID.search(href.replace('-', ''))
    if not match:
        return None
    h = match.group(1)
    return f'{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}'


def indent(text, spaces=4):
    pad = ' ' * spaces
    return '\n'.join(pad + line if line.strip() else '' for line in text.split('\n'))


def hard_breaks(text):
    """Переносы строк внутри абзаца из Notion — явные переносы в Markdown."""
    return '  \n'.join(line.rstrip() for line in text.split('\n'))


def _caption(text):
    return f'<p class="caption" markdown="1">{text}</p>'


_PYTHON = re.compile(r'^\s*(>>>|def |class |import |from \S+ import|print\(|for .+ in .+:|while .+:|if .+:|return\b|@\w+)', re.M)
_SQL = re.compile(r'^\s*(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|BEGIN|COMMIT|\w+=[#>]) ', re.M)
_SHELL = re.compile(r'^\s*(\$ |sudo |pip3? |git |python3? |cd |mkdir |source |django-admin )', re.M)


def guess_language(code):
    """Язык для блоков, помеченных в Notion как простой текст."""
    if _SQL.search(code):
        return 'sql'
    if _SHELL.search(code):
        return 'bash'
    if _PYTHON.search(code):
        return 'python'
    return 'text'


# ---------- блоки ----------

class MarkdownWriter:
    """Превращает блоки страницы в Markdown. Вложения складывает в `assets`."""

    def __init__(self, course, link_for_page, asset_name):
        self.course = course
        self.inline = InlineRenderer(link_for_page)
        self.asset_name = asset_name
        self.assets = {}  # имя файла -> (источник, id блока)

    def page(self, page):
        return self.blocks(page.blocks).strip() + '\n'

    def blocks(self, ids):
        out, previous, previous_text = [], None, ''
        for block_id in ids:
            block = self.course.blocks.get(block_id)
            if not block or block['type'] == 'page':
                continue
            kind = block['type']
            if kind == 'toggle' and not self.children(block).strip():
                # Раскрывающийся блок без содержимого — просто пункт списка.
                kind = 'bulleted_list'
                text = self._bulleted_list(block)
            else:
                text = self.block(block)
            if text is None or not text.strip():
                continue
            # Простые элементы одного списка — без пустой строки между ними.
            tight = previous == kind and kind in ('bulleted_list', 'numbered_list') \
                and '\n\n' not in text and '\n\n' not in previous_text
            out.append(('\n' if tight else '\n\n') + text if out else text)
            previous, previous_text = kind, text
        return ''.join(out)

    def children(self, block):
        return self.blocks(block.get('content') or [])

    def title(self, block):
        return self.inline(block.get('properties', {}).get('title'))

    def block(self, block):
        kind = block['type']
        handler = getattr(self, f'_{kind}', None)
        if handler:
            return handler(block)
        if kind in HEADINGS:
            text = f'{HEADINGS[kind]} {self.title(block).replace(chr(10), " ")}'
            children = self.children(block)
            return text + ('\n\n' + children if children else '')
        if kind in ('column_list', 'column', 'transclusion_container', 'transclusion_reference'):
            return self.children(block)
        # Неизвестный блок: сохраняем хотя бы текст.
        return hard_breaks(self.title(block)) + ('\n\n' + self.children(block) if block.get('content') else '')

    def _text(self, block):
        text = hard_breaks(self.title(block))
        children = self.children(block)
        return text + ('\n\n' + children if children else '')

    def _list_item(self, block, marker):
        text = hard_breaks(self.title(block)) or '&nbsp;'
        lines = text.split('\n')
        out = marker + lines[0] + ''.join('\n' + ' ' * 4 + line for line in lines[1:])
        children = self.children(block)
        if children:
            out += '\n\n' + indent(children)
        return out

    def _bulleted_list(self, block):
        return self._list_item(block, '-   ')

    def _numbered_list(self, block):
        return self._list_item(block, '1.  ')

    def _to_do(self, block):
        checked = block.get('properties', {}).get('checked', [['No']])[0][0] == 'Yes'
        return self._list_item(block, '-   ' + ('☑ ' if checked else '☐ '))

    def _quote(self, block):
        text = hard_breaks(self.title(block))
        children = self.children(block)
        if children:
            text += '\n\n' + children
        return '\n'.join('> ' + line if line else '>' for line in text.split('\n'))

    def _callout(self, block):
        icon = block.get('format', {}).get('page_icon', '')
        icon = icon if icon and not icon.startswith('http') else ''
        body = hard_breaks(self.title(block))
        children = self.children(block)
        if children:
            body += '\n\n' + children
        attr = f' data-icon="{icon}"' if icon else ''
        return f'<aside class="callout"{attr} markdown="1">\n\n{body}\n\n</aside>'

    def _toggle(self, block):
        summary = self.title(block).replace('\n', ' ')
        body = self.children(block)
        return f'<details markdown="1">\n<summary markdown="span">{summary}</summary>\n\n{body}\n\n</details>'

    def _code(self, block):
        props = block.get('properties', {})
        code = rich_plain(props.get('title')).replace('\t', '    ').rstrip()
        language = rich_plain(props.get('language')).strip().lower()
        language = CODE_LANGUAGES.get(language, language).replace(' ', '')
        fence = '```'
        while fence in code:
            fence += '`'
        caption = self.inline(props.get('caption'))
        if language in ('text', ''):
            language = guess_language(code)
        out = f'{fence}{language}\n{code}\n{fence}'
        return out + (f'\n\n{_caption(caption)}' if caption.strip() else '')

    def _divider(self, block):
        return '---'

    def _equation(self, block):
        return '```text\n' + rich_plain(block.get('properties', {}).get('title')) + '\n```'

    def _attachment(self, block, image):
        props = block.get('properties', {})
        source = rich_plain(props.get('source')) or block.get('format', {}).get('display_source', '')
        if not source:
            return None
        caption = self.inline(props.get('caption')).strip()
        name = self.asset_name(block, source, rich_plain(props.get('title')))
        self.assets[name] = (source, block['id'])
        if image:
            alt = re.sub(r'[\[\]*_`]', '', rich_plain(props.get('caption'))).strip()
            out = f'![{alt}](asset:{name})'
            return out + (f'\n\n{_caption(caption)}' if caption else '')
        title = escape(rich_plain(props.get('title')) or name)
        size = rich_plain(props.get('size'))
        return f'[📎 {title}](asset:{name})' + (f' — {size}' if size else '')

    def _image(self, block):
        return self._attachment(block, image=True)

    def _file(self, block):
        return self._attachment(block, image=False)

    _pdf = _file

    def _bookmark(self, block):
        props = block.get('properties', {})
        link = rich_plain(props.get('link'))
        title = rich_plain(props.get('title')) or link
        return f'[{escape(title)}]({link})' if link else None

    def _video(self, block):
        link = rich_plain(block.get('properties', {}).get('source'))
        return f'[▶ Видео]({link})' if link else None

    _embed = _video

    def _collection_view(self, block):
        table = self.course.collections.get(block['id'])
        if not table or not table['columns']:
            return None

        def cell(value, kind):
            if value is None:
                return ''
            if kind == 'checkbox':
                return '✓' if rich_plain(value) == 'Yes' else ''
            text = self.inline(value)
            return text.replace('|', '\\|').replace('\n', '<br>').strip()

        head = '| ' + ' | '.join(escape(c) for c in table['columns']) + ' |'
        rule = '| ' + ' | '.join('---' for _ in table['columns']) + ' |'
        rows = ['| ' + ' | '.join(cell(v, t) for v, t in zip(row, table['types'])) + ' |' for row in table['rows']]
        out = '\n'.join([head, rule, *rows])
        if table['name']:
            out = f'**{escape(table["name"])}**\n\n' + out
        return out

    _collection_view_page = _collection_view

    def _table(self, block):
        """Простая таблица Notion (не база данных)."""
        order = block.get('format', {}).get('table_block_column_order', [])
        rows = [self.course.blocks.get(i) for i in block.get('content') or []]
        rows = [r for r in rows if r]
        if not rows or not order:
            return None

        def line(row):
            props = row.get('properties', {})
            return '| ' + ' | '.join(self.inline(props.get(c)).replace('|', '\\|').replace('\n', '<br>') for c in order) + ' |'

        return '\n'.join([line(rows[0]), '| ' + ' | '.join('---' for _ in order) + ' |', *map(line, rows[1:])])


def build_structure(root):
    """
    Раскладывает дерево страниц на разделы и уроки.
    Возвращает [(раздел, [уроки])], где раздел и уроки — Page.
    """
    sections = []
    for section in root.children:
        lessons = []

        def collect(page):
            if page.has_content:
                lessons.append(page)
            for child in page.children:
                collect(child)

        if section.has_content:
            lessons.append(section)
        for child in section.children:
            collect(child)
        if lessons:
            sections.append((section, lessons))
    return sections


def assign_slugs(sections):
    used = set()
    for section, lessons in sections:
        section.slug = slugify(section.title) or section.id[:8]
    for section, lessons in sections:
        for page in lessons:
            base = slugify(page.title) or page.id[:8]
            slug = base
            if slug in used:
                slug = f'{base}-{section.slug}'
            n = 2
            while slug in used:
                slug = f'{base}-{n}'
                n += 1
            used.add(slug)
            page.slug = slug


def guess_extension(source, content_type, fallback=''):
    path = urllib.parse.urlparse(source).path
    ext = path.rsplit('.', 1)[-1].lower() if '.' in path.rsplit('/', 1)[-1] else ''
    if ext and len(ext) <= 5:
        return ext
    guessed = mimetypes.guess_extension((content_type or '').split(';')[0].strip())
    return (guessed or fallback).lstrip('.')
