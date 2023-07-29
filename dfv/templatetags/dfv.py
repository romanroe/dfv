from django import template
from django.templatetags.static import static
from django.utils.html import format_html

register = template.Library()


@register.simple_tag
def dfv():
    js = format_html(
        '<script type="text/javascript" defer src="{}"></script>',
        static("../static/dfv.js"),
    )
    return js
