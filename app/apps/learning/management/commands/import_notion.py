"""
Импорт курса из опубликованной страницы Notion.

    python manage.py import_notion https://geeksbackend.notion.site/Geeks-Backend-2b37c7cbcfe240198c1d522b045a69c3 \
        --course python-backend

Перезаписывает уроки курса и `course.json` (кроме полей, заданных вручную:
названия, описаний и порядка курса, описаний и отметок важных тем, а также исправленных
названий тем и уроков; темы с "manual": true сохраняются целиком) и скачивает вложения в
`static/learning/<course>/`. Ручные правки уроков после повторного импорта
пропадут — запускайте его, только пока основной текст живёт в Notion.
"""
import json
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ...content import CONTENT_DIR
from ...notion import (
    MarkdownWriter, NotionClient, NotionCourse, NotionError, assign_slugs, build_structure, guess_extension,
)
from ...text import slugify

PAGE_ID = re.compile(r'([0-9a-f]{32})(?:[?#].*)?$')

# Поля course.json, которые импорт не трогает, если они уже заполнены.
MANUAL_FIELDS = ('title', 'summary', 'description', 'level', 'order', 'outcomes')


def parse_url(url):
    match = re.match(r'^(https://[^/]+)/(.*)$', url.strip())
    if not match:
        raise CommandError('Ожидается ссылка вида https://<site>.notion.site/<страница>')
    page = PAGE_ID.search(match.group(2).replace('-', ''))
    if not page:
        raise CommandError('В ссылке не найден id страницы Notion')
    h = page.group(1)
    return match.group(1), f'{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}'


class Command(BaseCommand):
    help = 'Переносит курс из опубликованной страницы Notion в apps/learning/content/'
    # Импорт сам чинит контент, поэтому ошибки в нём не должны его блокировать.
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument('url', help='Ссылка на корневую страницу курса в Notion')
        parser.add_argument('--course', required=True, help='slug курса, например python-backend')
        parser.add_argument('--skip-assets', action='store_true', help='Не скачивать картинки и файлы')

    def handle(self, url, course, skip_assets, **options):
        if slugify(course) != course:
            raise CommandError('slug курса — латиница, цифры и дефис')
        site, root_id = parse_url(url)
        log = lambda message: self.stdout.write(message)  # noqa: E731

        log(f'Загружаю {url}')
        notion = NotionCourse(NotionClient(site), root_id, log=log)
        try:
            notion.load()
        except NotionError as e:
            raise CommandError(f'Notion не ответил: {e}') from e

        root = notion.page(root_id)
        sections = build_structure(root)
        if not sections:
            raise CommandError('На странице не найдено ни одного раздела с уроками')
        assign_slugs(sections)
        pages = {page.id: page for _, lessons in sections for page in lessons}

        def link_for_page(page_id):
            page = pages.get(page_id)
            if page:
                return page.title, f'lesson:{page.slug}'
            block = notion.blocks.get(page_id)
            title = ''.join(p[0] for p in (block or {}).get('properties', {}).get('title', []) if p)
            return title or 'страница', None

        def asset_name(block, source, title):
            stem = slugify(Path(title or source.split('?')[0].rsplit('/', 1)[-1]).stem)[:40] or 'file'
            ext = guess_extension(source.split('?')[0], '', 'bin')
            return f'{block["id"][:8]}-{stem}.{ext}'

        course_dir = CONTENT_DIR / course
        lessons_dir = course_dir / 'lessons'
        manifest_path = course_dir / 'course.json'
        manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}

        # Темы с "manual": true написаны прямо в репозитории, а не в Notion: их уроки не трогаем.
        manual_sections = [s for s in manifest.get('sections', []) if s.get('manual')]
        manual_files = {f'{l["slug"]}.md' for s in manual_sections for l in s.get('lessons', [])}
        lessons_dir.mkdir(parents=True, exist_ok=True)
        for path in lessons_dir.glob('*.md'):
            if path.name not in manual_files:
                path.unlink()

        writer = MarkdownWriter(notion, link_for_page, asset_name)
        for page in pages.values():
            (lessons_dir / f'{page.slug}.md').write_text(writer.page(page), encoding='utf-8')

        fresh = {
            'slug': course,
            'title': root.title,
            'summary': '',
            'description': [],
            'level': '',
            'order': 10,
            'outcomes': [],
            'source': url,
            'sections': [
                {
                    'slug': section.slug,
                    'title': section.title,
                    'icon': section.icon,
                    'summary': '',
                    'key': False,
                    'lessons': [{'slug': p.slug, 'title': p.title} for p in lessons],
                }
                for section, lessons in sections
            ],
        }
        for key in MANUAL_FIELDS:
            if manifest.get(key):
                fresh[key] = manifest[key]
        # Описания тем и названия, исправленные вручную, сохраняем по slug.
        summaries = {section['slug']: section.get('summary', '') for section in manifest.get('sections', [])}
        key_sections = {section['slug'] for section in manifest.get('sections', []) if section.get('key')}
        titles = {
            (kind, item['slug']): item['title']
            for section in manifest.get('sections', [])
            for kind, item in [('section', section), *(('lesson', lesson) for lesson in section.get('lessons', []))]
        }
        for section in fresh['sections']:
            section['title'] = titles.get(('section', section['slug']), section['title'])
            section['summary'] = summaries.get(section['slug'], '')
            section['key'] = section['slug'] in key_sections
            for lesson in section['lessons']:
                lesson['title'] = titles.get(('lesson', lesson['slug']), lesson['title'])
        # Ручные темы возвращаем на прежнее место — после той же темы, что и раньше.
        old_order = [section['slug'] for section in manifest.get('sections', [])]
        for manual in manual_sections:
            index = old_order.index(manual['slug'])
            before = next((slug for slug in reversed(old_order[:index]) if any(
                s['slug'] == slug for s in fresh['sections'])), None)
            position = next((i + 1 for i, s in enumerate(fresh['sections']) if s['slug'] == before), 0)
            fresh['sections'].insert(position, manual)
        manifest_path.write_text(json.dumps(fresh, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        log(f'Записано уроков: {len(pages)} в {len(sections)} разделах → {course_dir}')

        if skip_assets:
            return
        assets_dir = Path(settings.BASE_DIR) / 'static' / 'learning' / course
        assets_dir.mkdir(parents=True, exist_ok=True)
        failed = []
        for name, (source, block_id) in writer.assets.items():
            target = assets_dir / name
            if target.exists():
                continue
            try:
                data, _ = notion.client.download(source, block_id)
            except NotionError as e:
                failed.append((name, str(e)))
                continue
            target.write_bytes(data)
        log(f'Вложений: {len(writer.assets)}, не скачано: {len(failed)}')
        if failed:
            # Убираем из уроков ссылки на вложения, которых больше нет у источника.
            self.stderr.write('Убраны из уроков — источник недоступен:')
            for name, error in failed:
                self.stderr.write(f'  {name}: {error}')
            dead = '|'.join(re.escape(name) for name, _ in failed)
            pattern = re.compile(rf'!\[[^\]]*\]\(asset:(?:{dead})\)\n*|\[([^\]]*)\]\(asset:(?:{dead})\)')
            for path in lessons_dir.glob('*.md'):
                text = path.read_text(encoding='utf-8')
                fixed = pattern.sub(lambda m: m.group(1) or '', text)
                if fixed != text:
                    path.write_text(fixed, encoding='utf-8')
