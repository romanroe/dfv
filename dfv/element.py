import functools
import lxml.html

from typing import Any, Callable, cast, Optional, Tuple

from django.http import HttpResponse
from django_htmx.http import reswap, retarget

from dfv.utils import response_to_str
from dfv.view import view, VIEW_FN, ViewResponse


def split_content_and_swap_oob(content: str) -> Tuple[str, str]:
    if "hx-swap-oob" not in content.lower():
        return content, ""

    parsed: lxml.html.HtmlElement = lxml.html.fromstring(content)
    main = ""
    swaps = ""
    for el in parsed:
        el_str = str(lxml.html.tostring(el))
        if "hx-swap-oob" not in el.attrib:
            main += el_str
        else:
            swaps += el_str

    return main, swaps


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
        if no_element_wrap:
            return

        attr_id = f"id='{element_id}'" if element_id is not None else ""
        attr_hx_target = f"hx-target='{hx_target}'" if hx_target else ""
        attr_hx_swap = f"hx-swap='{hx_swap}'" if hx_swap else ""
        attr_classes = f"class='{classes}'" if classes else ""
        content = response_to_str(response)
        wrapped = (
            f"""<{tag} {attr_id} {attr_hx_target} {attr_hx_swap} {attr_classes}>"""
            f"""{content}"""
            f"""</{tag}>"""
        )

        response.content = bytes(wrapped, "UTF-8")
        super().__init__(response)


def body_response(response: HttpResponse, hx_swap="outerHTML") -> HttpResponse:
    response = retarget(response, "body")
    response = reswap(response, cast(Any, hx_swap))
    return ElementResponse(response, None, no_element_wrap=True)


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
