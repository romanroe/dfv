from django import template
from django.template import RequestContext
from django.templatetags.static import static
from django.utils.html import format_html

from dfv.route import get_path_name_for_view_callable, resolve_name
from dfv.view_stack import get_view_fn_call_stack_from_request_or_raise

register = template.Library()


@register.simple_tag
def dfv():
    js = format_html(
        '<script type="text/javascript" defer src="{}"></script>',
        static("../static/dfv.js"),
    )
    return js


@register.simple_tag(takes_context=True)
def view_url(context: RequestContext):
    stack = get_view_fn_call_stack_from_request_or_raise(context.request)
    name = get_path_name_for_view_callable(stack[-1])
    return resolve_name(name)
