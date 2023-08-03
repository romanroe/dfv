from typing import Callable, Literal

from django.test import RequestFactory
from django.urls import path, resolve


def create_resolved_request(
    view_fn: Callable, method=Literal["GET", "POST"], data=None
):
    factory = RequestFactory()
    urlpatterns = (path("view/", view_fn, name="a view"),)
    resolved = resolve("/view/", urlconf=urlpatterns)
    test_request = (
        factory.get("/view", data) if method == "GET" else factory.post("/view", data)
    )
    test_request.resolver_match = resolved
    return test_request
