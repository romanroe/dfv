import functools
from typing import Any, Callable, cast

from django.urls import (
    get_resolver,
    get_urlconf,
    path,
    reverse,
    URLPattern,
    URLResolver,
)


def get_path_name_for_view_callable(view: Callable) -> str:
    namespace: str = cast(Any, view).__module__
    namespace = namespace.replace(".", "-")
    return f"{namespace}-{view.__name__}"


def create_path(view: Callable, subroute: str | None = None, name: str | None = None):
    name = name if name is not None else get_path_name_for_view_callable(view)
    setattr(view, "__dfv_path_name__", name)
    subroute = subroute if subroute is not None else view.__name__
    return path(subroute, view, name=name)


def reverse_view(view: Callable, urlconf=None):
    urlconf = urlconf if urlconf is not None else get_urlconf()

    if hasattr(view, "__dfv_path_name__"):
        name = getattr(view, "__dfv_path_name__")
        return reverse(name, urlconf)

    resolver = get_resolver(urlconf)
    pattern = get_url_pattern_with_callback_list(resolver)
    if url_pattern := resolve_view_by_module_and_name(pattern, view):
        return "/" + resolver.reverse(url_pattern.callback)

    raise Exception(f"No match found for '{view}'.")


@functools.cache
def get_url_pattern_with_callback_list(resolver) -> list[URLPattern]:
    def list_pattern(url_pattern):
        for p in url_pattern:
            if isinstance(p, URLResolver):
                yield from list_pattern(p.url_patterns)
            elif isinstance(p, URLPattern) and hasattr(p, "callback"):
                yield p

    return list(list_pattern(resolver.url_patterns))


def resolve_view_by_module_and_name(url_pattern: list[URLPattern], view: Callable):
    name_lookup = get_path_name_for_view_callable(view)
    for u in url_pattern:
        name_pattern = get_path_name_for_view_callable(u.callback)
        if name_pattern == name_lookup:
            return u

    return None
