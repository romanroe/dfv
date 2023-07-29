import typing
from typing import Any, Optional
from unittest import TestCase

import django
from django import forms
from django.http import HttpResponse
from django.test import RequestFactory

from dfv import inject_args, param, param_get, param_post


class ParamsToArgsDecoratorTestCase(TestCase):
    factory: RequestFactory

    def setUp(self) -> None:
        self.factory = RequestFactory()
        django.setup()

    def test_without_type_annotation(self):
        @inject_args()
        def viewfn(
            _request,
            p1=param_get(),
            p2=param_get(),
        ):
            self.assertEqual(p1, "a")
            self.assertEqual(p2, "b")
            return HttpResponse("")

        result = viewfn(self.factory.get("/?p1=a&p2=b"))
        self.assertEqual(result.status_code, 200)

    def test_param_default_defines_target_type(self):
        @inject_args()
        def viewfn(_request, p1=param(default=123)):
            self.assertEqual(p1, 999)
            return HttpResponse("")

        result = viewfn(self.factory.get("/?p1=999"))
        self.assertEqual(result.status_code, 200)

    def test_missing_param_raises_exception(self):
        @inject_args()
        def viewfn(_request, p1=param_get()):
            self.assertEqual(p1, 1)

        def test():
            viewfn(self.factory.get("/"))

        self.assertRaises(Exception, test)

    def test_optional(self):
        @inject_args()
        def viewfn(
            _request,
            p1: str | None = param_get(),
            p2: Optional[str] = param_get(),
        ):
            self.assertEqual(p1, None)
            self.assertEqual(p2, None)

        viewfn(self.factory.get("/"))

    def test_optional_with_type_conversion(self):
        @inject_args()
        def viewfn(
            _request,
            p1: Optional[int] = param_get(),
        ):
            self.assertEqual(p1, 1)

        viewfn(self.factory.get("/?p1=1"))

    def test_type_conversion_int(self):
        @inject_args()
        def viewfn(_request, p1: int = param_get()):
            self.assertEqual(p1, 1)

        viewfn(self.factory.get("/?p1=1"))

    def test_type_conversion_float(self):
        @inject_args()
        def viewfn(_request, p1: float = param_get()):
            self.assertEqual(p1, 1.1)
            self.assertEqual(type(p1), float)

        viewfn(self.factory.get("/?p1=1.1"))

    def test_type_conversion_bool(self):
        @inject_args()
        def viewfn(
            _request,
            p1: bool = param_get(),
            p2: bool = param_get(),
            p3: bool = param_get(),
        ):
            self.assertEqual(p1, False)
            self.assertEqual(p2, False)
            self.assertEqual(p3, False)

        viewfn(self.factory.get("/?p1=false&p2=False&p3"))

    def test_type_conversion_list_unannotated(self):
        @inject_args()
        def viewfn(_request, p1: list = param_get()):
            self.assertEqual(type(p1), list)
            self.assertTrue("a" in p1)
            self.assertTrue("b" in p1)

        viewfn(self.factory.get("/?p1=a&p1=b"))

    def test_type_conversion_list_annotated(self):
        @inject_args()
        def viewfn(_request, p1: list[int] = param_get()):
            self.assertEqual(type(p1), list)
            self.assertTrue(1 in p1)
            self.assertTrue(2 in p1)

        viewfn(self.factory.get("/?p1=1&p1=2"))

    def test_post(self):
        @inject_args()
        def viewfn(
            _request,
            p1: str = param_post(),
            p2: str = param_post(),
        ):
            self.assertEqual(p1, "a")
            self.assertEqual(p2, "b")

        viewfn(self.factory.post("/", {"p1": "a", "p2": "b"}))

    def test_get_and_post_order(self):
        @inject_args()
        def viewfn(_request, p1: str = param()):
            self.assertEqual(p1, "a")

        viewfn(self.factory.post("/?p1=a", {"p1": "b"}))

    def test_function_call_arg_overrides_param(self):
        @inject_args()
        def viewfn(_request, p1: str = param()):
            self.assertEqual(p1, "b")

        viewfn(self.factory.get("/?p1=a"), "b")

    def test_function_call_kwarg_overrides_param(self):
        @inject_args()
        def viewfn(_request, p1: str = param()):
            self.assertEqual(p1, "b")

        viewfn(self.factory.get("/?p1=a"), p1="b")

    def test_param_consume_true(self):
        @inject_args()
        def viewfn(request, p1: str = param()):
            self.assertEqual(p1, "a")
            self.assertNotIn("p1", request.GET)

        viewfn(self.factory.get("/?p1=a"))

    def test_param_consume_false(self):
        @inject_args()
        def viewfn(request, p1: str = param(consume=False)):
            self.assertEqual(p1, "a")
            self.assertIn("p1", request.GET)

        viewfn(self.factory.get("/?p1=a"))

    def test_param_consume_get(self):
        @inject_args()
        def viewfn(request, p1: str = param_get()):
            self.assertEqual(p1, "a")
            self.assertNotIn("p1", request.GET)

        viewfn(self.factory.get("/?p1=a"))

    def test_param_consume_post(self):
        @inject_args()
        def viewfn(request, p1: str = param_post()):
            self.assertEqual(p1, "a")
            self.assertNotIn("p1", request.POST)

        viewfn(self.factory.post("/", {"p1": "a"}))

    def test_auto_default_value(self):
        @inject_args()
        def viewfn(_request, p1: str = param(default="a")):
            self.assertEqual(p1, "a")

        untyped_viewfn = typing.cast(Any, viewfn)
        untyped_viewfn(self.factory.get("/"))

    def test_auto_param_false(self):
        @inject_args(auto_param=False)
        def viewfn(_request, p1: str):
            self.assertEqual(p1, "a")

        untyped_viewfn = typing.cast(Any, viewfn)

        def test():
            untyped_viewfn(self.factory.get("/?p1=a"))

        self.assertRaisesRegex(
            Exception, "missing 1 required positional argument: 'p1'", test
        )

    def test_auto_param_true(self):
        @inject_args(auto_param=True)
        def viewfn(_request, p1: str):
            self.assertEqual(p1, "a")

        untyped_viewfn = typing.cast(Any, viewfn)
        untyped_viewfn(self.factory.get("/?p1=a"))

    def test_auto_param_get(self):
        @inject_args(auto_param="get")
        def viewfn(_request, p1: str):
            self.assertEqual(p1, "a")

        untyped_viewfn = typing.cast(Any, viewfn)
        untyped_viewfn(self.factory.get("/?p1=a"))

    def test_auto_param_get_does_not_receive_post_params(self):
        @inject_args(auto_param="get")
        def viewfn(_request, p1: str, p2="b"):
            self.assertEqual(p1, "a")
            self.assertEqual(p2, "b")

        untyped_viewfn = typing.cast(Any, viewfn)
        untyped_viewfn(self.factory.post("/?p1=a", {"p2": "x"}))

    def test_auto_param_post(self):
        @inject_args(auto_param="post")
        def viewfn(_request, p1: str):
            self.assertEqual(p1, "a")

        untyped_viewfn = typing.cast(Any, viewfn)
        untyped_viewfn(self.factory.post("/", {"p1": "a"}))

    def test_auto_param_post_does_not_receive_get_params(self):
        @inject_args(auto_param="post")
        def viewfn(_request, p1: str, p2="b"):
            self.assertEqual(p1, "a")
            self.assertEqual(p2, "b")

        untyped_viewfn = typing.cast(Any, viewfn)
        untyped_viewfn(self.factory.post("/p2=x", {"p1": "a"}))

    def test_auto_param_form(self):
        class TestForm(forms.Form):
            p1 = forms.TextInput()
            p2 = forms.TextInput()

        @inject_args()
        def viewfn(_request, form: TestForm):
            self.assertEqual(type(form), TestForm)

        untyped_viewfn = typing.cast(Any, viewfn)
        untyped_viewfn(self.factory.post("/", {"p1": "a", "p2": "b"}))

    def test_multiple_form_params_raises_exception(self):
        class TestForm(forms.Form):
            p1 = forms.TextInput()
            p2 = forms.TextInput()

        def test():
            @inject_args()
            def viewfn(_request, _form1: TestForm, _form2: TestForm):
                pass

        self.assertRaisesRegex(
            Exception, "You can only have one Form argument in a view function", test
        )

    def test_auto_param_form_is_false(self):
        class TestForm(forms.Form):
            p1 = forms.TextInput()
            p2 = forms.TextInput()

        @inject_args(auto_form=False)
        def viewfn(_request, form: Optional[TestForm] = None):
            self.assertEqual(None, form)

        viewfn(self.factory.post("/", {"p1": "a", "p2": "b"}))
