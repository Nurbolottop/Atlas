from django.shortcuts import redirect, render

from .content import get_course, get_courses
from .render import render_lesson
from .text import plural

UNKNOWN_COURSE = 'Такого курса нет. Возможно, адрес набран с ошибкой.'
UNKNOWN_SECTION = 'Такой темы нет в курсе. Возможно, адрес набран с ошибкой — загляните в программу.'
UNKNOWN_LESSON = 'Такого урока нет в курсе. Возможно, его переименовали — загляните в программу.'


def _not_found(request, message):
    return render(request, 'base/404.html', {'message': message}, status=404)


def course_stats(course):
    sources = [lesson.source for lesson in course.lessons.values()]
    examples = sum(text.count('\n```') + text.startswith('```') for text in sources) // 2
    hours = max(1, round(sum(section.minutes for section in course.sections) / 60))
    return [
        {'value': course.lesson_count, 'label': plural(course.lesson_count, ('урок', 'урока', 'уроков'))},
        {'value': len(course.sections), 'label': plural(len(course.sections), ('тема', 'темы', 'тем'))},
        {'value': examples, 'label': plural(examples, ('пример кода', 'примера кода', 'примеров кода'))},
        {'value': f'≈{hours}', 'label': plural(hours, ('час чтения', 'часа чтения', 'часов чтения'))},
    ]


def _lessons_json(course):
    """Названия и адреса уроков — для кнопки «Продолжить» и прогресса в браузере."""
    return {
        lesson.slug: {'title': lesson.title, 'url': lesson.url}
        for lesson in course.lessons.values()
    }


def index(request):
    return render(request, 'learning/index.html', {'courses': get_courses()})


def course_detail(request, course):
    course_obj = get_course(course)
    if course_obj is None:
        return _not_found(request, UNKNOWN_COURSE)
    query = request.GET.get('q', '').strip()[:100]
    return render(request, 'learning/course.html', {
        'course': course_obj,
        'stats': course_stats(course_obj),
        'query': query,
        'results': course_obj.search(query) if query else None,
        'lessons_json': _lessons_json(course_obj),
    })


def section_detail(request, course, section):
    course_obj = get_course(course)
    if course_obj is None:
        return _not_found(request, UNKNOWN_COURSE)
    section_obj = course_obj.get_section(section)
    if section_obj is None:
        # Старые адреса уроков были без темы: /learning/<курс>/<урок>/.
        lesson = course_obj.lessons.get(section)
        if lesson:
            return redirect(lesson.url, permanent=True)
        return _not_found(request, UNKNOWN_SECTION)
    return render(request, 'learning/section.html', {
        'course': course_obj,
        'section': section_obj,
        'lessons_json': _lessons_json(course_obj),
    })


def lesson_detail(request, course, section, lesson):
    course_obj = get_course(course)
    if course_obj is None:
        return _not_found(request, UNKNOWN_COURSE)
    lesson_obj = course_obj.lessons.get(lesson)
    if lesson_obj is None:
        return _not_found(request, UNKNOWN_LESSON)
    if lesson_obj.section.slug != section:
        return redirect(lesson_obj.url, permanent=True)
    html, toc = render_lesson(lesson_obj)
    return render(request, 'learning/lesson.html', {
        'course': course_obj,
        'lesson': lesson_obj,
        'content': html,
        'toc': toc,
    })
