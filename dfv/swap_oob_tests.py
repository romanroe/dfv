import lxml.html
import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from dfv import element
from dfv.htmx import swap_oob
from dfv.response_handler import hook_swap_oob
from dfv.utils import response_to_str
from dfv.view import ViewResponse


def test_append_swap_oob():
    original = HttpResponse("<div id='foo'>foo</foo>")
    oob = HttpResponse("<span id='oob'>oob</span>")
    response = ViewResponse(swap_oob(original, oob))
    parsed: lxml.html.HtmlElement = lxml.html.fromstring(response_to_str(response))
    assert parsed.attrib["id"] == "foo"
    assert parsed[0].attrib["id"] == "oob"
    assert parsed[0].attrib["hx-swap-oob"] == "outerHTML:#oob"


def test_append_swap_oob_multiple():
    original = HttpResponse("<div id='foo'>foo</div>")
    oob1 = HttpResponse("<span id='oob1'>oob1</span>")
    oob2 = HttpResponse("<span id='oob2'>oob2</span>")
    response = ViewResponse(swap_oob(original, [oob1, oob2]))
    parsed: lxml.html.HtmlElement = lxml.html.fromstring(response_to_str(response))
    assert parsed[0].attrib["id"] == "foo"
    assert parsed[1].attrib["id"] == "oob1"
    assert parsed[1].attrib["hx-swap-oob"] == "outerHTML:#oob1"
    assert parsed[2].attrib["id"] == "oob2"
    assert parsed[2].attrib["hx-swap-oob"] == "outerHTML:#oob2"


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


def test_append_swap_oob_child_element_return_parent_element(rf: RequestFactory):
    @element()
    def parent(_request):
        return HttpResponse("parent")

    @element()
    def child(request):
        hook_swap_oob(request, parent(request))
        return HttpResponse("child")

    response = child(rf.get("/"))
    parsed: lxml.html.HtmlElement = lxml.html.fromstring(response_to_str(response))
    assert parsed[0].attrib["id"] == "child"
    assert parsed[1].attrib["id"] == "parent"
    assert parsed[1].attrib["hx-swap-oob"] == "outerHTML:#parent"
