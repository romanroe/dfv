from unittest import TestCase

import django
import lxml.html
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.test import RequestFactory

from dfv import element, ElementResponse, response_to_str, swap_oob


class ElementDecoratorTestCase(TestCase):
    factory: RequestFactory

    def setUp(self) -> None:
        self.factory = RequestFactory()

    def _assert_default_values(self, response: HttpResponse):
        parsed: lxml.html.HtmlElement = lxml.html.fromstring(response_to_str(response))
        self.assertEqual(parsed.tag, "div")
        self.assertEqual(parsed.attrib["id"], "viewfn")
        self.assertEqual(parsed.attrib["hx-target"], "this")
        self.assertEqual(parsed.attrib["hx-swap"], "outerHTML")

    def test_without_braces(self):
        @element()
        def viewfn(_request):
            return HttpResponse("")

        result = viewfn(self.factory.get("/"))
        self._assert_default_values(result)

    def test_config(self):
        @element("foo", tag="span", hx_target="spam", hx_swap="egg")
        def viewfn(_request):
            return HttpResponse("body")

        response = viewfn(self.factory.get("/"))
        parsed: lxml.html.HtmlElement = lxml.html.fromstring(response_to_str(response))
        self.assertEqual(parsed.tag, "span")
        self.assertEqual(parsed.attrib["id"], "foo")
        self.assertEqual(parsed.attrib["hx-target"], "spam")
        self.assertEqual(parsed.attrib["hx-swap"], "egg")

    def test_append_swap_oob(self):
        original = HttpResponse("<div id='foo'>foo</foo>")
        oob = HttpResponse("<span id='oob'>oob</span>")
        response = swap_oob(original, oob)
        parsed: lxml.html.HtmlElement = lxml.html.fromstring(response_to_str(response))
        self.assertEqual(parsed.attrib["id"], "foo")
        self.assertEqual(parsed[0].attrib["id"], "oob")
        self.assertEqual(parsed[0].attrib["hx-swap-oob"], "outerHTML:#oob")

    def test_append_swap_oob_exception_if_additional_has_more_than_one_root_element(
        self,
    ):
        original = HttpResponse("<div id='foo'>foo</foo>")
        oob = HttpResponse("<span id='oob1'>oob1</span><span id='oob2'>oob2</span>")

        def test():
            swap_oob(original, oob)

        self.assertRaisesRegex(Exception, "one element", test)

    def test_swap_oob_exception_if_additional_has_no_id(
        self,
    ):
        original = HttpResponse("<div id='foo'>foo</foo>")
        oob = HttpResponse("<span>oob1</span>")

        def test():
            swap_oob(original, oob)

        self.assertRaisesRegex(Exception, "id attribute", test)

    def test_element_return_another_element(self):
        @element()
        def root(request):
            return child(request)

        @element()
        def child(_request):
            return HttpResponse("child")

        result = root(self.factory.get("/"))
        parsed: lxml.html.HtmlElement = lxml.html.fromstring(response_to_str(result))
        self.assertEqual(parsed.attrib["id"], "child")
        self.assertEqual(len(parsed.getchildren()), 0)

    def test_element_return_element_response(self):
        @element("unused")
        def viewfn(_request):
            return ElementResponse(HttpResponse("body"), "override")

        result = viewfn(self.factory.get("/"))
        parsed: lxml.html.HtmlElement = lxml.html.fromstring(response_to_str(result))
        self.assertEqual(parsed.attrib["id"], "override")

    def test_element_return_template_http_response(self):
        django.setup()

        @element()
        def viewfn(request):
            return TemplateResponse(
                request, "dfv/tests/TemplateResponse.html", {"foo": 123}
            )

        result = viewfn(self.factory.get("/"))
        print("result", result)
        parsed: lxml.html.HtmlElement = lxml.html.fromstring(response_to_str(result))
        self.assertEqual(parsed.attrib["id"], "viewfn")
        self.assertEqual(parsed.text.strip(), "123")
