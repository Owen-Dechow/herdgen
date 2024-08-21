from json import dumps
from django import template
from django.utils.safestring import mark_safe, SafeText
from ..models import AssignmentStep

register = template.Library()


@register.simple_tag()
def load_assignment_options() -> SafeText:
    options = AssignmentStep.CHOICES
    return mark_safe(f"<script>StepOptions = {dumps(options)}</script>")
