from typing import Callable, Optional, TypeAlias

from django.http import HttpRequest, HttpResponse

from dfv.view_stack import get_view_fn_call_stack_from_request_or_raise


HOOK: TypeAlias = Callable[[HttpResponse], Optional[HttpResponse]]


def get_response_handlers_from_request(request: HttpRequest) -> list[HOOK]:
    handlers = getattr(request, "__dfv_view_response_handlers", [])
    setattr(request, "__dfv_view_response_handlers", handlers)
    return handlers


def add_response_handler(request: HttpRequest, hook: HOOK):
    get_view_fn_call_stack_from_request_or_raise(request)
    handlers = get_response_handlers_from_request(request)
    handlers.append(hook)


def process_response(request: HttpRequest, response: HttpResponse) -> HttpResponse:
    handlers = get_response_handlers_from_request(request)
    for handler in handlers:
        result = handler(response)
        response = result if result is not None else response
    return response
