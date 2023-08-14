import json
import typing
from typing import Any

import pytest
from django import forms
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory
from django.urls import path, resolve

from dfv import handle_form, inject_args, view
from dfv.testutils import create_resolved_request


class TwoFieldForm(forms.Form):
    p1 = forms.CharField()
    p2 = forms.CharField()


def test_error_missing_form_type():
    def test():
        @view()
        def viewfn(_request, form=handle_form()):
            return HttpResponse(form)

    with pytest.raises(
        Exception,
        match=r"argument type for handle_form\(\) must be a subclass of django.forms.BaseForm",
    ):
        test()


def test_error_wrong_form_type():
    def test():
        @view()
        def viewfn(_request, _form: str = handle_form()):
            return HttpResponse("")

    with pytest.raises(
        Exception,
        match=r"argument type for handle_form\(\) must be a subclass of django.forms.BaseForm",
    ):
        test()


def test_form_explicit():
    @view()
    def viewfn(_request, form: TwoFieldForm = handle_form()):
        assert type(form) == TwoFieldForm
        return HttpResponse("")

    viewfn(create_resolved_request(viewfn, "POST", {"p1": "a", "p2": "b"}))


def test_form_implicit():
    @view()
    def viewfn(_request, form: TwoFieldForm):
        assert type(form) == TwoFieldForm
        return HttpResponse("")

    typing.cast(Any, viewfn)(
        create_resolved_request(viewfn, "POST", {"p1": "a", "p2": "b"})
    )


def test_form_get():
    @view()
    def viewfn(_request, form: TwoFieldForm = handle_form()):
        assert not form.is_bound
        assert not form.is_valid()
        return HttpResponse("")

    viewfn(create_resolved_request(viewfn, "GET", {"p1": "a", "p2": "b"}))


def test_form_post():
    @view()
    def viewfn(_request, form: TwoFieldForm = handle_form()):
        assert form.is_bound
        assert form.is_valid()
        assert form.cleaned_data["p1"] == "a"
        assert form.cleaned_data["p2"] == "b"
        return HttpResponse("")

    viewfn(create_resolved_request(viewfn, "POST", {"p1": "a", "p2": "b"}))


def test_initial():
    @inject_args(auto_param=True)
    def initial_fn(_request: HttpRequest, p1: str, p2: str):
        return {"p1": f"initial {p1}", "p2": f"initial {p2}"}

    @view()
    def viewfn(_request, form: TwoFieldForm = handle_form(initial=initial_fn)):
        assert form.initial["p1"] == "initial ia"
        assert form.initial["p2"] == "initial ib"
        return HttpResponse("")

    viewfn(create_resolved_request(viewfn, "GET", {"p1": "ia", "p2": "ib"}))


def test_form_patch(rf: RequestFactory):
    @view()
    def viewfn(_request, form: TwoFieldForm = handle_form()):
        assert form.is_bound
        assert not form.is_valid()
        return HttpResponse("")

    urlpatterns = (path("view/", viewfn, name="a view"),)
    resolved = resolve("/view/", urlconf=urlpatterns)
    request = rf.patch(
        "/",
        json.dumps({"p1": "", "p2": "b"}),
        "application/json",
        headers={"X-DFV-Validate-Field": "p1"},
    )
    request.resolver_match = resolved

    response = viewfn(request)
    assert response.status_code == 200
    assert response["Content-Type"] == "application/json"
    body = json.loads(response.content)
    assert body["name"] == "p1"
    field_p1 = body["fields"]["p1"]
    assert not field_p1["valid"]
    field_p2 = body["fields"]["p2"]
    assert field_p2["valid"]
