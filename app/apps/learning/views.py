from django.shortcuts import render

from .content import get_course, get_courses
from .render import render_lesson
from .text import plural

UNKNOWN_COURSE = 'Такого курса нет. Возможно, адрес набран с ошибкой.'
UNKNOWN_LESSON = 'Такого урока нет в курсе. Возможно, его переименовали — загляните в программу.'

READING_SPEED = 1300  # символов в минуту


def _not_found(request, message):
    return render(request, 'base/404.html', {'message': message}, status=404)


def course_stats(course):
    sources = [lesson.source for lesson in course.lessons.values()]
    examples = sum(text.count('\n```') + text.startswith('```') for text in sources) // 2
    hours = max(1, round(sum(len(text) for text in sources) / READING_SPEED / 60))
    return [
        {'value': course.lesson_count, 'label': plural(course.lesson_count, ('урок', 'урока', 'уроков'))},
        {'value': len(course.sections), 'label': plural(len(course.sections), ('раздел', 'раздела', 'разделов'))},
        {'value': examples, 'label': plural(examples, ('пример кода', 'примера кода', 'примеров кода'))},
        {'value': f'≈{hours}', 'label': plural(hours, ('час чтения', 'часа чтения', 'часов чтения'))},
    ]


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
    })


def lesson_detail(request, course, lesson):
    course_obj = get_course(course)
    if course_obj is None:
        return _not_found(request, UNKNOWN_COURSE)
    lesson_obj = course_obj.lessons.get(lesson)
    if lesson_obj is None:
        return _not_found(request, UNKNOWN_LESSON)
    html, toc = render_lesson(lesson_obj)
    return render(request, 'learning/lesson.html', {
        'course': course_obj,
        'lesson': lesson_obj,
        'content': html,
        'toc': toc,
        'progress': round(lesson_obj.number / course_obj.lesson_count * 100),
    })
