import functools
from typing import Callable, cast, Optional, TypeVar

import wrapt
from django.contrib.auth import decorators as auth_decorators
from django.http import HttpRequest, HttpResponse

from dfv.inject_args import inject_args
from dfv.response_handler import process_response
from dfv.utils import response_to_str
from dfv.view_stack import get_view_fn_call_stack_from_request

VIEW_FN = TypeVar("VIEW_FN", bound=Callable[..., HttpResponse])


class ViewResponse(wrapt.ObjectProxy):
    def __init__(self, response: HttpResponse | None):
        if response is not None:
            content = response_to_str(response)
            bcontent = bytes(content, "UTF-8")
            dfv_swap_oob = getattr(response, "_dfv_swap_oob", [])
            for oob in dfv_swap_oob:
                bcontent += oob
            response.content = bcontent

        super().__init__(response)

    def __str__(self):
        return response_to_str(self)


def view(
    *,
    decorators: Optional[list[Callable]] = None,
    login_required=False,
    handle_args=True,
) -> Callable[[VIEW_FN], VIEW_FN]:
    if decorators is None:
        decorators = []

    if login_required:
        decorators = [auth_decorators.login_required(), *decorators]

    def decorator(fn: VIEW_FN) -> VIEW_FN:
        if handle_args:
            fn = inject_args()(fn)

        if decorators is not None:
            for d in reversed(decorators):
                fn = d(fn)

        @functools.wraps(fn)
        def inner(*args, **kwargs) -> HttpResponse:
            view_request: HttpRequest = args[0]
            stack = get_view_fn_call_stack_from_request(view_request)
            try:
                stack.append(fn)
                result = fn(*args, **kwargs)
                if result is not None and len(stack) == 1:
                    result = process_response(view_request, result)

                return (
                    ViewResponse(result)
                    if not isinstance(result, ViewResponse)
                    else result
                )
            finally:
                stack.pop()

        return cast(VIEW_FN, inner)

    return decorator
