import django
import lxml.html
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.test import RequestFactory

from dfv import element, ElementResponse
from dfv.element import ElementMeta
from dfv.utils import response_to_str


def _assert_default_values(response: HttpResponse):
    parsed: lxml.html.HtmlElement = lxml.html.fromstring(response_to_str(response))
    assert parsed.tag == "div"
    assert parsed.attrib["id"] == "viewfn"
    assert parsed.attrib["hx-target"] == "this"
    assert parsed.attrib["hx-swap"] == "outerHTML"


def test_without_braces(rf: RequestFactory):
    @element()
    def viewfn(_request):
        return HttpResponse("")

    result = viewfn(rf.get("/"))
    _assert_default_values(result)


def test_config(rf: RequestFactory):
    @element("foo", tag="span", hx_target="spam", hx_swap="egg")
    def viewfn(_request):
        return HttpResponse("body")

    response = viewfn(rf.get("/"))
    parsed: lxml.html.HtmlElement = lxml.html.fromstring(response_to_str(response))
    assert parsed.tag == "span"
    assert parsed.attrib["id"] == "foo"
    assert parsed.attrib["hx-target"] == "spam"
    assert parsed.attrib["hx-swap"] == "egg"


def test_element_return_another_element(rf: RequestFactory):
    @element()
    def root(request):
        return child(request)

    @element()
    def child(_request):
        return HttpResponse("child")

    result = root(rf.get("/"))
    parsed: lxml.html.HtmlElement = lxml.html.fromstring(response_to_str(result))
    assert parsed.attrib["id"] == "child"
    assert len(parsed.getchildren()) == 0


def test_element_return_element_response(rf: RequestFactory):
    @element("unused")
    def viewfn(_request):
        return ElementResponse.wrap(
            HttpResponse("body"), ElementMeta(element_id="override")
        )

    result = viewfn(rf.get("/"))
    parsed: lxml.html.HtmlElement = lxml.html.fromstring(response_to_str(result))
    assert parsed.attrib["id"] == "override"


def test_element_return_template_http_response(rf: RequestFactory):
    django.setup()

    @element()
    def viewfn(request):
        return TemplateResponse(
            request, "dfv/tests/TemplateResponse.html", {"foo": 123}
        )

    result = viewfn(rf.get("/"))
    parsed: lxml.html.HtmlElement = lxml.html.fromstring(response_to_str(result))
    assert parsed.attrib["id"] == "viewfn"
    assert parsed.text.strip() == "123"


def test_classes(rf: RequestFactory):
    @element(attrs={"class": "foo bar"})
    def viewfn(_request):
        return HttpResponse("body")

    response = viewfn(rf.get("/"))
    parsed: lxml.html.HtmlElement = lxml.html.fromstring(response_to_str(response))
    assert parsed.attrib["class"] == "foo bar"
