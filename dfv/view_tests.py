import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import path, resolve

import dfv
from dfv.testutils import create_resolved_request
from dfv.view_stack import (
    get_view_fn_call_stack_from_request,
    is_view_fn_stack_at_root,
)


def test_str(rf: RequestFactory):
    @dfv.view()
    def view1(_request):
        return HttpResponse("response")

    response = str(view1(rf.get("/")))
    assert response == "response"


def test_call_stack(rf: RequestFactory):
    @dfv.view()
    def view1(request):
        stack = get_view_fn_call_stack_from_request(request)
        assert len(stack) == 1
        view2(request)
        assert len(stack) == 1
        return HttpResponse("")

    @dfv.view()
    def view2(request):
        stack = get_view_fn_call_stack_from_request(request)
        assert len(stack) == 2
        return HttpResponse("")

    view1(rf.get("/"))


def test_is_view_fn_target():
    @dfv.view()
    def view1(request):
        assert is_view_fn_stack_at_root(request)
        return HttpResponse("")

    view1(create_resolved_request(view1))


def test_is_view_fn_target_nested_view(rf: RequestFactory):
    @dfv.view()
    def view1(request):
        assert is_view_fn_stack_at_root(request)
        view2(request)
        return HttpResponse("")

    @dfv.view()
    def view2(request):
        assert not is_view_fn_stack_at_root(request)
        return HttpResponse("")

    urlpatterns = (path("view/", view1, name="a view"),)
    resolved = resolve("/view/", urlconf=urlpatterns)
    test_request = rf.post("/view")
    test_request.resolver_match = resolved
    view1(test_request)


def test_is_view_fn_target_nested_view_ignore_target(rf: RequestFactory):
    @dfv.view()
    def view1(request):
        assert dfv.is_post(request)
        view2(request)
        return HttpResponse("")

    @dfv.view()
    def view2(request):
        assert dfv.is_post(request, ignore_view_stack=True)
        return HttpResponse("")

    urlpatterns = (path("view/", view1, name="a view"),)
    resolved = resolve("/view/", urlconf=urlpatterns)
    test_request = rf.post("/view")
    test_request.resolver_match = resolved
    view1(test_request)


def test_is_view_fn_target_raw_view(rf: RequestFactory):
    def view1(request):
        assert is_view_fn_stack_at_root(request)
        return HttpResponse("")

    urlpatterns = (path("view/", view1, name="a view"),)
    resolved = resolve("/view/", urlconf=urlpatterns)
    test_request = rf.post("/view")
    test_request.resolver_match = resolved

    def fn():
        view1(test_request)

    with pytest.raises(
        Exception, match="This function can only be called from within a DFV view."
    ):
        fn()
