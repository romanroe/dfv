import json
from typing import Any
from unittest import TestCase

import django
import typing
from django import forms
from django.http import HttpResponse
from django.test import RequestFactory

from dfv import inject_args, handle_form


class TestForm(forms.Form):
    p1 = forms.CharField()
    p2 = forms.CharField()


class ParamsToArgsDecoratorTestCase(TestCase):
    factory: RequestFactory

    def setUp(self) -> None:
        self.factory = RequestFactory()
        django.setup()

    def test_error_missing_form_type(self):
        def test():
            @inject_args()
            def viewfn(_request, form=handle_form()):
                return HttpResponse(form)

        self.assertRaisesRegex(
            Exception,
            "argument type for handle_form\(\) must be a subclass of django.forms.BaseForm",
            test,
        )

    def test_error_wrong_form_type(self):
        def test():
            @inject_args()
            def viewfn(_request, _form: str = handle_form()):
                return HttpResponse("")

        self.assertRaisesRegex(
            Exception,
            "argument type for handle_form\(\) must be a subclass of django.forms.BaseForm",
            test,
        )

    def test_form_explicit(self):
        @inject_args()
        def viewfn(_request, form: TestForm = handle_form()):
            self.assertEqual(type(form), TestForm)
            return HttpResponse("")

        viewfn(self.factory.post("/", {"p1": "a", "p2": "b"}))

    def test_form_implicit(self):
        @inject_args()
        def viewfn(_request, form: TestForm):
            self.assertEqual(type(form), TestForm)
            return HttpResponse("")

        typing.cast(Any, viewfn)(self.factory.post("/", {"p1": "a", "p2": "b"}))

    def test_form_get(self):
        @inject_args()
        def viewfn(_request, form: TestForm = handle_form()):
            self.assertFalse(form.is_bound)
            self.assertFalse(form.is_valid())
            return HttpResponse("")

        viewfn(self.factory.get("/"))

    def test_form_post(self):
        @inject_args()
        def viewfn(_request, form: TestForm = handle_form()):
            self.assertTrue(form.is_bound)
            self.assertTrue(form.is_valid())
            self.assertEqual(form.cleaned_data["p1"], "a")
            self.assertEqual(form.cleaned_data["p2"], "b")
            return HttpResponse("")

        viewfn(self.factory.post("/", {"p1": "a", "p2": "b"}))

    def test_form_patch(self):
        @inject_args()
        def viewfn(_request, form: TestForm = handle_form()):
            self.assertTrue(form.is_bound)
            self.assertFalse(form.is_valid())
            return HttpResponse("")

        request = self.factory.patch(
            "/",
            json.dumps({"p1": "", "p2": "b"}),
            "application/json",
            headers={"X-DFV-Validate-Field": "p1"},
        )
        response = viewfn(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        body = json.loads(response.content)
        self.assertEqual(body["name"], "p1")
        field_p1 = body["fields"]["p1"]
        self.assertEqual(field_p1["valid"], False)
        field_p2 = body["fields"]["p2"]
        self.assertEqual(field_p2["valid"], True)
