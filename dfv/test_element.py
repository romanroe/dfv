import django
import lxml.html
import pytest
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.test import RequestFactory

from dfv import element, ElementResponse, response_to_str, swap_oob


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


def test_append_swap_oob():
    original = HttpResponse("<div id='foo'>foo</foo>")
    oob = HttpResponse("<span id='oob'>oob</span>")
    response = swap_oob(original, oob)
    parsed: lxml.html.HtmlElement = lxml.html.fromstring(response_to_str(response))
    assert parsed.attrib["id"] == "foo"
    assert parsed[0].attrib["id"] == "oob"
    assert parsed[0].attrib["hx-swap-oob"] == "outerHTML:#oob"


def test_append_swap_oob_exception_if_additional_has_more_than_one_root_element():
    original = HttpResponse("<div id='foo'>foo</foo>")
    oob = HttpResponse("<span id='oob1'>oob1</span><span id='oob2'>oob2</span>")

    def test():
        swap_oob(original, oob)

    with pytest.raises(Exception, match="one element"):
        test()


def test_swap_oob_exception_if_additional_has_no_id():
    original = HttpResponse("<div id='foo'>foo</foo>")
    oob = HttpResponse("<span>oob1</span>")

    def test():
        swap_oob(original, oob)

    with pytest.raises(Exception, match="id attribute"):
        test()


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
        return ElementResponse(HttpResponse("body"), "override")

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
    @element(classes="foo bar")
    def viewfn(_request):
        return HttpResponse("body")

    response = viewfn(rf.get("/"))
    parsed: lxml.html.HtmlElement = lxml.html.fromstring(response_to_str(response))
    assert parsed.attrib["class"] == "foo bar"
