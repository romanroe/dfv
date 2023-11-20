import json

from django import forms, template
from django.db.models import Model
from django.template import RequestContext
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.safestring import mark_safe

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


def _args_kwargs_to_json_dict(context: RequestContext, args, kwargs):
    for a in args:
        if isinstance(a, Model):
            a = model_to_dict(a)
        if not isinstance(a, dict):
            raise ValueError(
                f"{context.template_name}: positional arguments must be dicts or Django models"
            )
        kwargs = {**a, **kwargs}

    return json.dumps(kwargs)


@register.simple_tag(takes_context=True)
def hx_vals(context: RequestContext, *args, **kwargs):
    j = _args_kwargs_to_json_dict(context, args, kwargs)
    attr = f" hx-vals='{j}' "
    return mark_safe(attr)


@register.filter
def model_to_dict(model):
    return forms.model_to_dict(model)


@register.filter
def asstr(model):
    return str(model)


@register.simple_tag(takes_context=True)
def view_url(context: RequestContext):
    stack = get_view_fn_call_stack_from_request_or_raise(context.request)
    view = stack[-1]
    return reverse_view(view)
