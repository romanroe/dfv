from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory
from django.urls import path

from dfv import view
from dfv.route import create_path, get_path_name_for_view_callable, resolve_view


def view1(_request: HttpRequest):
    return HttpResponse("")


def test_without_type_annotation():
    assert get_path_name_for_view_callable(view1) == "dfv-route_tests-view1"


def test_resolve_view(rf: RequestFactory):
    @view()
    def viewfn(_request):
        return HttpResponse("OK")

    urlpatterns = (create_path(viewfn),)
    resolved = resolve_view(viewfn, urlconf=urlpatterns)
    request = rf.get("/")
    request.resolver_match = resolved
    response = viewfn(request)
    assert response.content == b"OK"


def test_resolve_view_with_custom_name(rf: RequestFactory):
    @view()
    def viewfn(_request):
        return HttpResponse("OK")

    urlpatterns = (create_path(viewfn, name="custom"),)
    resolved = resolve_view(viewfn, urlconf=urlpatterns)
    request = rf.get("/")
    request.resolver_match = resolved
    response = viewfn(request)
    assert response.content == b"OK"


def test_resolve_view_by_module_and_name(rf: RequestFactory):
    @view()
    def viewfn(_request):
        return HttpResponse("OK")

    urlpatterns = (path("/viewfn/", viewfn, name="viewfn"),)
    resolved = resolve_view(viewfn, urlconf=urlpatterns)
    request = rf.get("/")
    request.resolver_match = resolved
    response = viewfn(request)
    assert response.content == b"OK"
