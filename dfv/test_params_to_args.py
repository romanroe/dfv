import typing
from typing import Any, Optional

import pytest
from django import forms
from django.http import HttpResponse
from django.test import RequestFactory

from dfv import inject_args, param, param_get, param_post, view
from dfv.testutils import create_resolved_request


def test_without_type_annotation(rf: RequestFactory):
    @view()
    def viewfn(
        _request,
        p1=param_get(),
        p2=param_get(),
    ):
        assert p1 == "a"
        assert p2 == "b"
        return HttpResponse("")

    result = viewfn(rf.get("/?p1=a&p2=b"))
    assert result.status_code == 200


def test_param_default_defines_target_type(rf: RequestFactory):
    @view()
    def viewfn(_request, p1=param(default=123)):
        assert p1 == 999
        return HttpResponse("")

    result = viewfn(rf.get("/?p1=999"))
    assert result.status_code == 200


def test_missing_param_raises_exception(rf: RequestFactory):
    @view()
    def viewfn(_request, p1=param_get()):
        assert p1 == 1

    def test():
        viewfn(rf.get("/"))

    with pytest.raises(Exception):
        test()


def test_optional(rf: RequestFactory):
    @view()
    def viewfn(
        _request,
        p1: str | None = param_get(),
        p2: Optional[str] = param_get(),
    ):
        assert p1 is None
        assert p2 is None

    viewfn(rf.get("/"))


def test_optional_with_type_conversion(rf: RequestFactory):
    @view()
    def viewfn(
        _request,
        p1: Optional[int] = param_get(),
    ):
        assert p1 == 1

    viewfn(rf.get("/?p1=1"))


def test_type_conversion_int(rf: RequestFactory):
    @view()
    def viewfn(_request, p1: int = param_get()):
        assert p1 == 1

    viewfn(rf.get("/?p1=1"))


def test_type_conversion_float(rf: RequestFactory):
    @view()
    def viewfn(_request, p1: float = param_get()):
        assert p1 == 1.1
        assert type(p1) == float

    viewfn(rf.get("/?p1=1.1"))


def test_type_conversion_bool(rf: RequestFactory):
    @view()
    def viewfn(
        _request,
        p1: bool = param_get(),
        p2: bool = param_get(),
        p3: bool = param_get(),
    ):
        assert not p1
        assert not p2
        assert not p3

    viewfn(rf.get("/?p1=false&p2=False&p3"))


def test_type_conversion_list_unannotated(rf: RequestFactory):
    @view()
    def viewfn(_request, p1: list = param_get()):
        assert type(p1) == list
        assert "a" in p1
        assert "b" in p1

    viewfn(rf.get("/?p1=a&p1=b"))


def test_type_conversion_list_annotated(rf: RequestFactory):
    @view()
    def viewfn(_request, p1: list[int] = param_get()):
        assert type(p1) == list
        assert 1 in p1
        assert 2 in p1

    viewfn(rf.get("/?p1=1&p1=2"))


def test_post(rf: RequestFactory):
    @view()
    def viewfn(
        _request,
        p1: str = param_post(),
        p2: str = param_post(),
    ):
        assert p1 == "a"
        assert p2 == "b"

    viewfn(rf.post("/", {"p1": "a", "p2": "b"}))


def test_get_and_post_order(rf: RequestFactory):
    @view()
    def viewfn(_request, p1: str = param()):
        assert p1 == "a"

    viewfn(rf.post("/?p1=a", {"p1": "b"}))


def test_function_call_arg_overrides_param(rf: RequestFactory):
    @view()
    def viewfn(_request, p1: str = param()):
        assert p1 == "b"

    viewfn(rf.get("/?p1=a"), "b")


def test_function_call_kwarg_overrides_param(rf: RequestFactory):
    @view()
    def viewfn(_request, p1: str = param()):
        assert p1 == "b"

    viewfn(rf.get("/?p1=a"), p1="b")


def test_param_consume_true(rf: RequestFactory):
    @view()
    def viewfn(request, p1: str = param()):
        assert p1 == "a"
        assert "p1" not in request.GET

    viewfn(rf.get("/?p1=a"))


def test_param_consume_false(rf: RequestFactory):
    @view()
    def viewfn(request, p1: str = param(consume=False)):
        assert p1 == "a"
        assert "p1" in request.GET

    viewfn(rf.get("/?p1=a"))


def test_param_consume_get(rf: RequestFactory):
    @view()
    def viewfn(request, p1: str = param_get()):
        assert p1 == "a"
        assert "p1" not in request.GET

    viewfn(rf.get("/?p1=a"))


def test_param_consume_post(rf: RequestFactory):
    @view()
    def viewfn(request, p1: str = param_post()):
        assert p1 == "a"
        assert "p1" not in request.POST

    viewfn(rf.post("/", {"p1": "a"}))


def test_auto_default_value(rf: RequestFactory):
    @view()
    def viewfn(_request, p1: str = param(default="a")):
        assert p1 == "a"

    untyped_viewfn = typing.cast(Any, viewfn)
    untyped_viewfn(rf.get("/"))


def test_auto_param_false(rf: RequestFactory):
    @inject_args(auto_param=False)
    def viewfn(_request, p1: str):
        assert p1 == "a"

    untyped_viewfn = typing.cast(Any, viewfn)

    def test():
        untyped_viewfn(rf.get("/?p1=a"))

    with pytest.raises(Exception, match="missing 1 required positional argument: 'p1'"):
        test()


def test_auto_param_true(rf: RequestFactory):
    @inject_args(auto_param=True)
    def viewfn(_request, p1: str):
        assert p1 == "a"

    untyped_viewfn = typing.cast(Any, viewfn)
    untyped_viewfn(rf.get("/?p1=a"))


def test_auto_param_get(rf: RequestFactory):
    @inject_args(auto_param="get")
    def viewfn(_request, p1: str):
        assert p1 == "a"

    untyped_viewfn = typing.cast(Any, viewfn)
    untyped_viewfn(rf.get("/?p1=a"))


def test_auto_param_get_does_not_receive_post_params(rf: RequestFactory):
    @inject_args(auto_param="get")
    def viewfn(_request, p1: str, p2="b"):
        assert p1 == "a"
        assert p2 == "b"

    untyped_viewfn = typing.cast(Any, viewfn)
    untyped_viewfn(rf.post("/?p1=a", {"p2": "x"}))


def test_auto_param_post(rf: RequestFactory):
    @inject_args(auto_param="post")
    def viewfn(_request, p1: str):
        assert p1 == "a"

    untyped_viewfn = typing.cast(Any, viewfn)
    untyped_viewfn(rf.post("/", {"p1": "a"}))


def test_auto_param_post_does_not_receive_get_params(rf: RequestFactory):
    @inject_args(auto_param="post")
    def viewfn(_request, p1: str, p2="b"):
        assert p1 == "a"
        assert p2 == "b"

    untyped_viewfn = typing.cast(Any, viewfn)
    untyped_viewfn(rf.post("/p2=x", {"p1": "a"}))


def test_auto_param_form():
    class TestForm(forms.Form):
        p1 = forms.TextInput()
        p2 = forms.TextInput()

    @view()
    def viewfn(_request, form: TestForm):
        assert type(form) == TestForm

    untyped_viewfn = typing.cast(Any, viewfn)
    untyped_viewfn(create_resolved_request(viewfn, "POST", {"p1": "a", "p2": "b"}))


def test_multiple_form_params_raises_exception():
    class TestForm(forms.Form):
        p1 = forms.TextInput()
        p2 = forms.TextInput()

    def test():
        @view()
        def viewfn(_request, _form1: TestForm, _form2: TestForm):
            pass

    with pytest.raises(
        Exception, match="You can only have one Form argument in a view function"
    ):
        test()


def test_auto_param_form_is_false(rf: RequestFactory):
    class TestForm(forms.Form):
        p1 = forms.TextInput()
        p2 = forms.TextInput()

    @inject_args(auto_form=False)
    def viewfn(_request, form: Optional[TestForm] = None):
        assert form is None

    viewfn(rf.post("/", {"p1": "a", "p2": "b"}))
