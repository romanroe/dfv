from typing import Any

from django.http import HttpRequest, HttpResponseBase, QueryDict
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe, SafeString


def querydict_key_removed(querydict: dict, key) -> QueryDict:
    temp = QueryDict(mutable=True)
    temp.update(querydict)
    del temp[key]
    return temp


def _get_request_from_args(args: list[Any]) -> HttpRequest:
    return args[0]


def response_to_str(response: HttpResponseBase | TemplateResponse) -> SafeString:
    if isinstance(response, TemplateResponse):
        response = response.render()

    return mark_safe(str(response.content, "utf-8"))
