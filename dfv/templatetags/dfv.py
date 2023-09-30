from django import template
from django.template import RequestContext
from django.templatetags.static import static
from django.utils.html import format_html

from dfv.route import reverse_view
from dfv.view_stack import get_view_fn_call_stack_from_request_or_raise

register = template.Library()


@register.simple_tag
def dfv():
    return format_html(
        '<script type="text/javascript" defer src="{}"></script>',
        static("../static/dfv.js"),
    )


@register.simple_tag
def dfv_script_swap_merge():
    return format_html(
        '<script type="text/javascript" defer src="{}"></script>',
        static("../static/dfv_swap_merge.js"),
    )


@register.simple_tag(takes_context=True)
def view_url(context: RequestContext):
    stack = get_view_fn_call_stack_from_request_or_raise(context.request)
    view = stack[-1]
    return reverse_view(view)
