import functools
from typing import Any, Callable, cast, Optional

import wrapt
from django.http import HttpRequest, HttpResponse
from django_htmx.http import reswap, retarget

from dfv.utils import response_to_str
from dfv.view import view, VIEW_FN, ViewResponse


# def split_content_and_swap_oob(content: str) -> Tuple[str, str]:
#     if "hx-swap-oob" not in content.lower():
#         return content, ""
#
#     parsed: lxml.html.HtmlElement = lxml.html.fromstring(content)
#     main = ""
#     swaps = ""
#     for el in parsed:
#         el_str = str(lxml.html.tostring(el))
#         if "hx-swap-oob" not in el.attrib:
#             main += el_str
#         else:
#             swaps += el_str
#
#     return main, swaps


class ElementRequest(wrapt.ObjectProxy, HttpRequest):
    def __init__(
        self,
        wrapped: HttpRequest,
        element_id: Optional[str] = None,
        tag="div",
        hx_target="this",
        hx_swap="outerHTML",
        attrs: dict[str, str] | None = None,
    ):
        super().__init__(wrapped)
        self._self_element_id = element_id
        self._self_tag = tag
        self._self_hx_target = hx_target
        self._self_hx_swap = hx_swap
        self._self_attrs = attrs if attrs is not None else {}
        self._self_nowrap = False

    @property
    def element_id(self):
        return self._self_element_id

    @element_id.setter
    def element_id(self, value):
        self._self_element_id = value

    @property
    def tag(self):
        return self._self_tag

    @tag.setter
    def tag(self, value):
        self._self_tag = value

    @property
    def hx_target(self):
        return self._self_hx_target

    @hx_target.setter
    def hx_target(self, value):
        self._self_hx_target = value

    @property
    def hx_swap(self):
        return self._self_hx_swap

    @hx_swap.setter
    def hx_swap(self, value):
        self._self_hx_swap = value

    @property
    def attrs(self):
        return self._self_attrs

    @attrs.setter
    def attrs(self, value):
        self._self_attrs = value

    @property
    def nowrap(self):
        return self._self_nowrap

    @nowrap.setter
    def nowrap(self, value):
        self._self_nowrap = value


class ElementResponse(ViewResponse):
    @staticmethod
    def empty() -> HttpResponse:
        return ElementResponse(HttpResponse())

    @staticmethod
    def wrap_response(response: HttpResponse) -> HttpResponse:
        return ElementResponse(response)

    @staticmethod
    def wrap_element_response(
        request: ElementRequest, response: HttpResponse
    ) -> HttpResponse:
        if request.nowrap:
            return response

        attr_id = f"id='{request.element_id}'" if request.element_id is not None else ""
        attr_hx_target = f"hx-target='{request.hx_target}'" if request.hx_target else ""
        attr_hx_swap = f"hx-swap='{request.hx_swap}'" if request.hx_swap else ""
        attrs_str = " ".join(f'{k}="{v}"' for k, v in request.attrs.items())
        content = response_to_str(response)
        wrapped = (
            f"""<{request.tag} {attr_id} {attr_hx_target} {attr_hx_swap} {attrs_str}>"""
            f"""{content}"""
            f"""</{request.tag}>"""
        )
        response.content = bytes(wrapped, "UTF-8")

        return ElementResponse(response)

    def __init__(self, response: HttpResponse):
        super().__init__(response)


def body_response(response: HttpResponse, hx_swap="outerHTML") -> HttpResponse:
    response = retarget(response, "body")
    response = reswap(response, cast(Any, hx_swap))
    return ElementResponse.wrap_response(response)


def element(
    element_id: Optional[str] = None,
    *,
    tag="div",
    hx_target="this",
    hx_swap="outerHTML",
    attrs: dict[str, str] | None = None,
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
            request: HttpRequest = args[0]
            element_request = ElementRequest(
                request, id, tag, hx_target, hx_swap, attrs
            )
            response = f(element_request, *args[1:], **kwargs)
            if not response["Content-Type"].startswith("text/html"):
                return response

            if isinstance(response, ElementResponse):
                return response

            return ElementResponse.wrap_element_response(element_request, response)

        return cast(VIEW_FN, inner)

    return decorator
