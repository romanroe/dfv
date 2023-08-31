from typing import cast, TypeVar

from django.forms import BaseForm
from django.http import HttpRequest

from dfv import is_get, is_post

T_FORM = TypeVar("T_FORM", bound=BaseForm)


def create_form(request: HttpRequest, form_class: type[T_FORM], **kwargs) -> T_FORM:
    if is_get(request):
        form = form_class(**kwargs)
    else:
        form = form_class(data=request.POST, files=request.FILES, **kwargs)
    return cast(T_FORM, form)


def is_valid_submit(request: HttpRequest, form: BaseForm) -> bool:
    return is_post(request) and form.is_valid()
