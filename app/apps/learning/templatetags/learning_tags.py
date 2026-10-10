from django import template

from ..content import get_courses
from ..text import plural

register = template.Library()


@register.simple_tag
def first_course():
    courses = get_courses()
    return courses[0] if courses else None


@register.filter
def ru_plural(value, forms):
    """{{ n|ru_plural:"урок,урока,уроков" }} -> «урока» для 3."""
    return plural(int(value), forms.split(','))
