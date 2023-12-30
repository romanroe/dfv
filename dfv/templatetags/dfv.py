import json

from django import forms, template
from django.db.models import Model
from django.template import RequestContext
from django.template.base import kwarg_re
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from dfv.route import reverse_view as reverse_view_fn

register = template.Library()


@register.simple_tag
def dfv_script():
    return format_html(
        '<script type="text/javascript" defer src="{}"></script>',
        static("../static/dfv.js"),
    )


@register.simple_tag
def dfv_behavior_form_state():
    return mark_safe(
        """
        <script type="text/hyperscript">
            behavior FormState
                def form_state()
                    send form_state(state:me as Values)
                end
                init form_state()
                then on input form_state()
            end
        </script>
        """,
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
def to_str(model):
    return str(model)


@register.tag()
def reverse_view(parser, token):
    parts = token.split_contents()[1:]
    if len(parts) > 3 and parts[-2] == "as":
        viewfn, params, var_name = parts[0], parts[1:-2], parts[-1]
    else:
        viewfn, params, var_name = parts[0], parts[1:], None

    args = []
    kwargs = {}
    for p in params:
        m = kwarg_re.match(p)
        name, value = m.groups()
        value = parser.compile_filter(value)
        if name:
            kwargs[name] = value
        else:
            args.append(value)

    return ReverseViewNode(viewfn, args, kwargs, var_name)


class ReverseViewNode(template.Node):
    def __init__(self, viewfn, args, kwargs, var_name):
        self.viewfn = template.Variable(viewfn)
        self.args = args
        self.kwargs = kwargs
        self.var_name = var_name

    def render(self, context):
        viewfn_var = self.viewfn.resolve(context)
        args = [arg.resolve(context) for arg in self.args]
        kwargs = {k: v.resolve(context) for k, v in self.kwargs.items()}

        url = reverse_view_fn(viewfn_var, None, None, args=args, kwargs=kwargs)
        if self.var_name:
            context[self.var_name] = url
            return ""
        return url
