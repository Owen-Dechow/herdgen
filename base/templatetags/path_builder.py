from typing import Any
from django import template
from django.utils.safestring import mark_safe, SafeText

from .animal_filters import auto_filter_text

register = template.Library()


def clean(text: str) -> str:
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


@register.simple_tag(takes_context=True)
def build_class_path(context: dict[str, Any], classes: str) -> SafeText:
    connectedclass = context.get("class", None)
    if connectedclass is None:
        connectedclass = context.get("connectedclass")

    return mark_safe(
        f'<a href="/class/{connectedclass.id}" class="{classes}">{clean(connectedclass.name)}/</a>'
    )


@register.simple_tag(takes_context=True)
def build_enrollments_path(context: dict[str, Any], classes: str) -> SafeText:
    connectedclass = context.get("class", None)
    if connectedclass is None:
        connectedclass = context.get("connectedclass")

    return mark_safe(
        f'<a href="/class/{connectedclass.id}/enrollments" class="{classes}">Enrollments/</a>'
    )


@register.simple_tag(takes_context=True)
def build_assignments_path(context: dict[str, Any], classes: str) -> SafeText:
    connectedclass = context.get("class", None)
    if connectedclass is None:
        connectedclass = context.get("connectedclass")

    return mark_safe(
        f'<a href="/class/{connectedclass.id}/assignments" class="{classes}">Assignments/</a>'
    )


@register.simple_tag(takes_context=True)
def build_assignment_path(context: dict[str, Any], classes: str) -> SafeText:
    connectedclass = context.get("class", None)
    if connectedclass is None:
        connectedclass = context.get("connectedclass")

    assignment = context["assignment"]

    return mark_safe(
        f'<a href="/class/{connectedclass.id}/assignments/{assignment.id}" class="{classes}">{clean(assignment.name)}/</a>'
    )


@register.simple_tag(takes_context=True)
def build_herd_path(context: dict[str, Any], classes: str) -> SafeText:
    connectedclass = context.get("class", None)
    if connectedclass is None:
        connectedclass = context.get("connectedclass")

    herd_auth = context["herd_auth"]

    herd_name = auto_filter_text(context, herd_auth.herd.name)
    return mark_safe(
        f'<a href="/class/{connectedclass.id}/herd/{herd_auth.herd.id}" class="{classes}">{clean(herd_name)}/</a>'
    )
