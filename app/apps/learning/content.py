"""
Загрузка курсов сервиса «Обучение».

Каждый курс — папка в `content/`:

    content/<course>/course.json        — название, описание, разделы и порядок уроков
    content/<course>/lessons/<slug>.md  — текст урока в Markdown

Картинки и файлы уроков лежат в `static/learning/<course>/`, в тексте на них
ссылаются как `asset:<имя файла>`, на другие уроки — как `lesson:<slug>`.

Чтобы добавить урок, положите Markdown-файл и впишите его в нужный раздел
`course.json`. Структура проверяется функцией `validate()` — она подключена
к `manage.py check`.
"""
import json
import re
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.urls import reverse

from .text import normalize

CONTENT_DIR = Path(__file__).resolve().parent / 'content'
ASSETS_DIR = Path(settings.BASE_DIR) / 'static' / 'learning'

ASSET_RE = re.compile(r'asset:([^\s)"\'<>]+)')
LESSON_RE = re.compile(r'lesson:([a-z0-9-]+)')
SLUG_RE = re.compile(r'^[a-z0-9][a-z0-9-]*$')

COURSE_FIELDS = {'slug': str, 'title': str, 'summary': str, 'description': list, 'sections': list}

READING_SPEED = 1300  # символов в минуту


class ContentError(Exception):
    pass


class Lesson:
    def __init__(self, course, section, data, number):
        self.course = course
        self.section = section
        self.slug = data['slug']
        self.title = data['title']
        self.number = number  # сквозной номер в курсе, с 1
        self.prev = None
        self.next = None

    def __repr__(self):
        return f'<Lesson {self.course.slug}/{self.slug}>'

    @property
    def path(self):
        return self.course.dir / 'lessons' / f'{self.slug}.md'

    @property
    def source(self):
        return self.path.read_text(encoding='utf-8')

    @property
    def search_text(self):
        return normalize(f'{self.title} {self.section.title} {_plain(self.source)}')

    @property
    def url(self):
        return reverse('learning:lesson', args=[self.course.slug, self.section.slug, self.slug])

    @property
    def minutes(self):
        return max(1, round(len(self.source) / READING_SPEED))

    @property
    def excerpt(self):
        """Первый абзац урока — анонс для страницы темы."""
        for block in re.split(r'\n\s*\n', self.source):
            block = block.strip()
            if not block or block[0] in '#`|<>!-*0123456789' or block.startswith('['):
                continue
            text = ' '.join(_plain(block).split())
            if len(text) < 40:
                continue
            if len(text) > 180:
                text = text[:180].rsplit(' ', 1)[0].rstrip('.,;:—-') + '…'
            return text
        return ''

    @property
    def title_text(self):
        return normalize(f'{self.title} {self.section.title}')


class Section:
    """Тема курса: группа уроков со своей страницей."""

    def __init__(self, course, data, number):
        self.course = course
        self.number = number
        self.slug = data['slug']
        self.title = data['title']
        self.icon = data.get('icon', '')
        self.summary = data.get('summary', '')
        self.lessons = []
        self.prev = None
        self.next = None

    def __repr__(self):
        return f'<Section {self.course.slug}/{self.slug}>'

    @property
    def url(self):
        return reverse('learning:section', args=[self.course.slug, self.slug])

    @property
    def minutes(self):
        return sum(lesson.minutes for lesson in self.lessons)

    @property
    def lesson_slugs(self):
        return ' '.join(lesson.slug for lesson in self.lessons)


class Course:
    def __init__(self, data, directory):
        self.data = data
        self.dir = directory
        self.slug = data['slug']
        self.title = data['title']
        self.summary = data.get('summary', '')
        self.description = data.get('description', [])
        self.level = data.get('level', '')
        self.outcomes = data.get('outcomes', [])
        self.order = data.get('order', 100)
        self.sections = []
        self.lessons = {}

        number = 0
        previous = None
        for index, section_data in enumerate(data['sections'], 1):
            section = Section(self, section_data, index)
            if self.sections:
                section.prev = self.sections[-1]
                self.sections[-1].next = section
            for lesson_data in section_data.get('lessons', []):
                number += 1
                lesson = Lesson(self, section, lesson_data, number)
                if lesson.slug in self.lessons:
                    raise ContentError(f'{self.slug}/course.json: урок «{lesson.slug}» указан дважды')
                lesson.prev = previous
                if previous:
                    previous.next = lesson
                previous = lesson
                section.lessons.append(lesson)
                self.lessons[lesson.slug] = lesson
            self.sections.append(section)

    def get_section(self, slug):
        return next((s for s in self.sections if s.slug == slug), None)

    @property
    def first_lesson(self):
        return next(iter(self.lessons.values()), None)

    @property
    def lesson_count(self):
        return len(self.lessons)

    def search(self, query):
        """Уроки, где встречаются все слова запроса; совпадения в названии — выше."""
        words = normalize(query).split()
        if not words:
            return []
        found = [lesson for lesson in self.lessons.values() if all(w in lesson.search_text for w in words)]
        return sorted(found, key=lambda l: (not all(w in l.title_text for w in words), l.number))


def _plain(markdown_text):
    text = re.sub(r'```.*?```', ' ', markdown_text, flags=re.S)
    text = re.sub(r'<[^>]+>|!\[[^\]]*\]\([^)]*\)', ' ', text)
    text = re.sub(r'\]\([^)]*\)', ' ', text)
    return re.sub(r'[\\*_`#>\[\]|]', ' ', text)


def _read_json(path):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ContentError(f'{path.parent.name}/{path.name}: некорректный JSON — {e}') from e


def _load():
    courses = {}
    for path in sorted(CONTENT_DIR.glob('*/course.json')):
        data = _read_json(path)
        for key, expected in COURSE_FIELDS.items():
            if not isinstance(data.get(key), expected):
                raise ContentError(f'{path.parent.name}/course.json: нет поля «{key}» или оно неверного типа')
        if data['slug'] != path.parent.name:
            raise ContentError(f'{path.parent.name}/course.json: slug «{data["slug"]}» не совпадает с папкой')
        courses[data['slug']] = Course(data, path.parent)
    return dict(sorted(courses.items(), key=lambda kv: (kv[1].order, kv[0])))


@lru_cache(maxsize=1)
def _cached():
    return _load()


def store():
    # В режиме разработки перечитываем файлы на каждый запрос,
    # чтобы правки текста были видны без перезапуска.
    if settings.DEBUG:
        return _load()
    return _cached()


def get_courses():
    return list(store().values())


def get_course(slug):
    return store().get(slug)


def validate():
    """Проверяет курсы. Возвращает (errors, warnings)."""
    errors, warnings = [], []
    try:
        courses = _load()
    except (ContentError, OSError, KeyError) as e:
        return [str(e)], []

    for course in courses.values():
        prefix = f'{course.slug}/course.json'
        if not SLUG_RE.match(course.slug):
            errors.append(f'{prefix}: недопустимый slug курса')
        if not course.lessons:
            errors.append(f'{prefix}: в курсе нет уроков')
        if not course.summary:
            warnings.append(f'{prefix}: не заполнено краткое описание (summary)')

        section_slugs = set()
        for section in course.sections:
            if not section.title or not SLUG_RE.match(section.slug or ''):
                errors.append(f'{prefix}: у раздела «{section.title}» нет названия или slug')
            if section.slug in section_slugs:
                errors.append(f'{prefix}: раздел «{section.slug}» указан дважды')
            section_slugs.add(section.slug)
            if not section.lessons:
                warnings.append(f'{prefix}: в разделе «{section.title}» нет уроков')

        listed = set()
        for lesson in course.lessons.values():
            listed.add(lesson.path.name)
            where = f'{course.slug}/lessons/{lesson.slug}.md'
            if not SLUG_RE.match(lesson.slug) or not lesson.title:
                errors.append(f'{prefix}: у урока «{lesson.slug}» неверный slug или нет названия')
            if not lesson.path.exists():
                errors.append(f'{prefix}: нет файла урока {where}')
                continue
            source = lesson.source
            for target in set(LESSON_RE.findall(source)):
                if target not in course.lessons:
                    errors.append(f'{where}: ссылка на неизвестный урок «{target}»')
            for name in set(ASSET_RE.findall(source)):
                if not (ASSETS_DIR / course.slug / name).exists():
                    errors.append(f'{where}: нет файла static/learning/{course.slug}/{name}')

        for path in (course.dir / 'lessons').glob('*.md'):
            if path.name not in listed:
                warnings.append(f'{course.slug}/lessons/{path.name}: файл не указан в course.json')

    return errors, warnings

