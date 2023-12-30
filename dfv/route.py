from inspect import signature, Signature
from typing import Any, Callable, cast
from uuid import UUID

from django.urls import (
    path,
    reverse,
)


def get_path_name_for_view_callable(view: Callable, include_module=True) -> str:
    if not include_module:
        return view.__name__

    namespace: str = cast(Any, view).__module__
    namespace = namespace.replace(".", "-")
    return f"{namespace}-{view.__name__}"


def create_path(
    viewfn,
    *,
    name: str | None = None,
    url: str | None = None,
    include_module_name=True,
):
    ps = list(signature(viewfn).parameters.values())[1:]
    url_params = ""
    for p in ps:
        if p.default is not Signature.empty:
            break

        url_params += "<"
        if p.annotation is UUID:
            url_params += "uuid"
        elif p.annotation is int:
            url_params += "int"
        elif p.annotation is str or p.annotation is Signature.empty:
            url_params += "str"
        else:
            raise Exception(f"can not handle type {p.annotation}")
        url_params += f":{p.name}>/"

    if url == "":
        url = url_params
    else:
        url = viewfn.__name__ + "/" + url_params
    path_name = name or get_path_name_for_view_callable(viewfn, include_module_name)

    setattr(viewfn, "__dfv_path_name__", path_name)
    setattr(viewfn, "__dfv_path_url__", url)

    return path(url, viewfn, name=path_name)


# def create_path(view: Callable, subroute: str | None = None, name: str | None = None):
#     name = name if name is not None else get_path_name_for_view_callable(view)
#     setattr(view, "__dfv_path_name__", name)
#     subroute = subroute if subroute is not None else view.__name__
#     return path(subroute, view, name=name)


def reverse_view(
    view: Callable, urlconf=None, current_app=None, args=None, kwargs=None
):
    if not (path_name := getattr(view, "__dfv_path_name__", None)):
        raise Exception("This view was not registered with create_path().")

    return reverse(
        path_name, urlconf=urlconf, current_app=current_app, args=args, kwargs=kwargs
    )


# @functools.cache
# def get_url_pattern_with_callback_list(resolver) -> list[URLPattern]:
#     def list_pattern(url_pattern):
#         for p in url_pattern:
#             if isinstance(p, URLResolver):
#                 yield from list_pattern(p.url_patterns)
#             elif isinstance(p, URLPattern) and hasattr(p, "callback"):
#                 yield p
#
#     return list(list_pattern(resolver.url_patterns))
#
#
# def resolve_view_by_module_and_name(url_pattern: list[URLPattern], view: Callable):
#     name_lookup = get_path_name_for_view_callable(view)
#     for u in url_pattern:
#         name_pattern = get_path_name_for_view_callable(u.callback)
#         if name_pattern == name_lookup:
#             return u
#
#     return None
