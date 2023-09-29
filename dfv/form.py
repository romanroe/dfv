from typing import cast, TypeVar

from django.forms import BaseForm
from django.http import HttpRequest, QueryDict

from dfv import is_get, is_head, is_patch, is_post
from dfv.view_stack import is_view_fn_request_target

T_FORM = TypeVar("T_FORM", bound=BaseForm)


def _convert_querydict_to_initial_values(qd: QueryDict) -> dict[str, str]:
    return {k: v for k, v in qd.items()}


def create_form(request: HttpRequest, form_class: type[T_FORM], **kwargs) -> T_FORM:
    if is_get(request) or is_head(request) or not is_view_fn_request_target(request):
        form = form_class(**kwargs)
    elif is_patch(request):
        qd = QueryDict(request.body, encoding=request.encoding)
        initial = _convert_querydict_to_initial_values(qd)
        form = form_class(initial=initial, **kwargs)
    else:
        form = form_class(data=request.POST, files=request.FILES, **kwargs)
    return cast(T_FORM, form)


def is_valid_submit(request: HttpRequest, form: BaseForm) -> bool:
    return is_post(request) and form.is_valid()
