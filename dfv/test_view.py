from unittest import TestCase

from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import path, resolve

import dfv
from dfv import get_view_fn_call_stack_from_request
from dfv.testutils import create_resolved_request


class ViewDecoratorTestCase(TestCase):
    factory: RequestFactory

    def setUp(self) -> None:
        self.factory = RequestFactory()

    def test_call_stack(self):
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

        view1(self.factory.get("/"))

    def test_is_view_fn_target(self):
        @dfv.view()
        def view1(request):
            assert dfv.is_view_fn_request_target(request)
            return HttpResponse("")

        view1(create_resolved_request(view1))

    def test_is_view_fn_target_nested_view(self):
        @dfv.view()
        def view1(request):
            assert dfv.is_view_fn_request_target(request)
            view2(request)
            return HttpResponse("")

        @dfv.view()
        def view2(request):
            assert not dfv.is_view_fn_request_target(request)
            return HttpResponse("")

        urlpatterns = (path("view/", view1, name="a view"),)
        resolved = resolve("/view/", urlconf=urlpatterns)
        test_request = self.factory.post("/view")
        test_request.resolver_match = resolved
        view1(test_request)

    def test_is_view_fn_target_nested_view_ignore_target(self):
        @dfv.view()
        def view1(request):
            assert dfv.is_post(request)
            view2(request)
            return HttpResponse("")

        @dfv.view()
        def view2(request):
            assert dfv.is_post(request, ignore_resolved_view=True)
            return HttpResponse("")

        urlpatterns = (path("view/", view1, name="a view"),)
        resolved = resolve("/view/", urlconf=urlpatterns)
        test_request = self.factory.post("/view")
        test_request.resolver_match = resolved
        view1(test_request)

    def test_is_view_fn_target_raw_view(self):
        def view1(request):
            assert dfv.is_view_fn_request_target(request)
            return HttpResponse("")

        urlpatterns = (path("view/", view1, name="a view"),)
        resolved = resolve("/view/", urlconf=urlpatterns)
        test_request = self.factory.post("/view")
        test_request.resolver_match = resolved

        def fn():
            view1(test_request)

        self.assertRaisesRegex(
            Exception, "This function can only be called from within a DFV view.", fn
        )
