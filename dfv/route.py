from typing import Any, Callable, cast

from django.urls import NoReverseMatch, path, reverse_lazy


def get_path_name_for_view_callable(view: Callable) -> str:
    namespace: str = cast(Any, view).__module__
    namespace = namespace.replace(".", "-")
    return f"{namespace}-{view.__name__}"


def create_path(view: Callable, subpath: str | None = None):
    name = get_path_name_for_view_callable(view)
    subpath = subpath if subpath is not None else view.__name__
    return path(subpath, view, name=name)


def resolve_name(name: str, urlconf=None):
    try:
        return reverse_lazy(name, urlconf=urlconf)
    except NoReverseMatch as e:
        raise Exception(
            f"No match found for '{name}'. Did you use create_route() to add the view to urlpattern?"
        ) from e


def resolve_view(view: Callable, urlconf=None):
    name = get_path_name_for_view_callable(view)
    return resolve_name(name, urlconf)
