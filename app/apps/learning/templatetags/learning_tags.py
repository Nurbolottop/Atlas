from django import template

from ..content import get_courses

register = template.Library()


@register.simple_tag
def first_course():
    courses = get_courses()
    return courses[0] if courses else None
