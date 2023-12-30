from typing import cast, TypeVar

from django.forms import BaseForm
from django.http import HttpRequest, QueryDict

from dfv import is_patch, is_post, is_put
from dfv.view_stack import is_view_fn_stack_at_root

T_FORM = TypeVar("T_FORM", bound=BaseForm)


def _convert_querydict_to_initial_values(qd: QueryDict) -> dict[str, str]:
    return {k: v for k, v in qd.items()}


def create_form(request: HttpRequest, form_class: type[T_FORM], **kwargs) -> T_FORM:
    if not is_view_fn_stack_at_root(request):
        form = form_class(**kwargs)
    elif is_patch(request):
        qd = QueryDict(request.body, encoding=request.encoding)

        initial = {}
        if "initial" in kwargs:
            initial = kwargs["initial"]
            del kwargs["initial"]
        initial_from_query = _convert_querydict_to_initial_values(qd)
        initial.update(initial_from_query)

        form = form_class(initial=initial, **kwargs)
    elif is_post(request) or is_put(request):
        form = form_class(data=request.POST, files=request.FILES, **kwargs)
    else:
        form = form_class(**kwargs)
    return cast(T_FORM, form)


def is_valid_submit(request: HttpRequest, form: BaseForm) -> bool:
    return is_post(request) and form.is_valid()
