import typing
from typing import Callable

from django.http import HttpRequest


@typing.overload
def get_view_fn_call_stack_from_request(request: HttpRequest) -> list[Callable]:
    ...


@typing.overload
def get_view_fn_call_stack_from_request(
    request: HttpRequest, create: bool
) -> typing.Optional[list[Callable]]:
    ...


def get_view_fn_call_stack_from_request(
    request: HttpRequest, create=True
) -> typing.Optional[list[Callable]]:
    call_stack = getattr(request, "__dfv_view_fn_call_stack", None)
    call_stack = [] if call_stack is None and create else call_stack
    setattr(request, "__dfv_view_fn_call_stack", call_stack)
    return call_stack


def get_view_fn_call_stack_from_request_or_raise(
    request: HttpRequest,
) -> list[Callable]:
    stack = get_view_fn_call_stack_from_request(request, create=False)
    if stack is None or len(stack) == 0:
        raise Exception("This function can only be called from within a DFV view.")
    return stack


def is_view_fn_request_target(request: HttpRequest) -> bool:
    stack = get_view_fn_call_stack_from_request_or_raise(request)
    if len(stack) != 1:
        return False

    called_view: Callable = stack[0]
    return str(called_view.__qualname__) == str(
        request.resolver_match.func.__qualname__
    )


def is_head(request: HttpRequest, ignore_resolved_view=True) -> bool:
    return (
        ignore_resolved_view or is_view_fn_request_target(request)
    ) and request.method == "HEAD"


def is_get(request: HttpRequest, ignore_resolved_view=True) -> bool:
    return (
        ignore_resolved_view or is_view_fn_request_target(request)
    ) and request.method == "GET"


def is_post(request: HttpRequest, ignore_resolved_view=False) -> bool:
    return (
        ignore_resolved_view or is_view_fn_request_target(request)
    ) and request.method == "POST"


def is_put(request: HttpRequest, ignore_resolved_view=False) -> bool:
    return (
        ignore_resolved_view or is_view_fn_request_target(request)
    ) and request.method == "PUT"


def is_patch(request: HttpRequest, ignore_resolved_view=False) -> bool:
    return (
        ignore_resolved_view or is_view_fn_request_target(request)
    ) and request.method == "PATCH"


def is_delete(request: HttpRequest, ignore_resolved_view=False) -> bool:
    return (
        ignore_resolved_view or is_view_fn_request_target(request)
    ) and request.method == "DELETE"
