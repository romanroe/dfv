import functools
from typing import Any, Callable, cast, Optional

from django.http import HttpResponse
from django_htmx.http import reswap, retarget

from dfv.utils import response_to_str
from dfv.view import view, VIEW_FN, ViewResponse


class ElementResponse(ViewResponse):
    @staticmethod
    def empty() -> HttpResponse:
        return ElementResponse(HttpResponse(), None, no_element_wrap=True)

    def __init__(
        self,
        response: HttpResponse,
        element_id: Optional[str],
        tag="div",
        hx_target="this",
        hx_swap="outerHTML",
        classes: Optional[str] = None,
        no_element_wrap=False,
    ):
        if not no_element_wrap:
            attr_id = f"id='{element_id}'" if element_id is not None else ""
            attr_hx_target = f"hx-target='{hx_target}'" if hx_target else ""
            attr_hx_swap = f"hx-swap='{hx_swap}'" if hx_swap else ""
            attr_classes = f"class='{classes}'" if classes else ""
            new_content = (
                f"""<{tag} {attr_id} {attr_hx_target} {attr_hx_swap} {attr_classes}>"""
                f"""{response_to_str(response)}"""
                f"""</{tag}>"""
            )
            response.content = bytes(new_content, "UTF-8")

        super().__init__(response)

    def __str__(self):
        return response_to_str(self)


def body_response(response: HttpResponse, hx_swap="outerHTML") -> HttpResponse:
    response = retarget(response, "body")
    response = reswap(response, cast(Any, hx_swap))
    return ElementResponse(response, None, no_element_wrap=True)


# noinspection PyShadowingNames
def element(
    element_id: Optional[str] = None,
    *,
    tag="div",
    hx_target="this",
    hx_swap="outerHTML",
    classes: Optional[str] = None,
    handle_args=True,
    decorators: Optional[list[Callable]] = None,
    login_required=False,
) -> Callable[[VIEW_FN], VIEW_FN]:
    def decorator(f: VIEW_FN) -> VIEW_FN:
        id = element_id if isinstance(element_id, str) else f.__name__
        f = view(
            handle_args=handle_args,
            decorators=decorators,
            login_required=login_required,
        )(f)

        @functools.wraps(f)
        def inner(*args, **kwargs) -> HttpResponse:
            response = f(*args, **kwargs)
            if not response["Content-Type"].startswith("text/html"):
                return response

            if isinstance(response, ElementResponse):
                return response

            return ElementResponse(
                response,
                element_id=id,
                tag=tag,
                hx_target=hx_target,
                hx_swap=hx_swap,
                classes=classes,
            )

        return cast(VIEW_FN, inner)

    return decorator
