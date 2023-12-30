import typing
from typing import Any, Optional
from urllib.parse import urlencode
from uuid import uuid4

import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.test import RequestFactory

from dfv import inject_params, param
from dfv.inject_params import ObjectDoesNotExistWithPk
from main.models import AppUser


def test_without_type_annotation(rf: RequestFactory):
    @inject_params()
    def viewfn(
        _request,
        p1=param(),
        p2=param(),
    ):
        assert p1 == "aaa"
        assert p2 == "bbb"
        return HttpResponse("")

    result = viewfn(rf.get("/?p1=aaa&p2=bbb"))
    assert result.status_code == 200


def test_param_default_defines_target_type(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1=param(default=123)):
        assert p1 == 999
        return HttpResponse("")

    result = viewfn(rf.get("/?p1=999"))
    assert result.status_code == 200


def test_missing_param_raises_exception(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1=param()):
        assert p1 == 1

    def test():
        viewfn(rf.get("/"))

    with pytest.raises(Exception):
        test()


def test_optional(rf: RequestFactory):
    @inject_params()
    def viewfn(
        _request,
        p1: Optional[str] = param(),
    ):
        assert p1 is None

    viewfn(rf.get("/"))


def test_optional_as_union(rf: RequestFactory):
    @inject_params()
    def viewfn(
        _request,
        p1: str | None = param(),
    ):
        assert p1 is None

    viewfn(rf.get("/"))


def test_optional_with_type_conversion(rf: RequestFactory):
    @inject_params()
    def viewfn(
        _request,
        p1: Optional[int] = param(),
    ):
        assert p1 == 1

    viewfn(rf.get("/?p1=1"))


def test_type_conversion_int(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1: int = param()):
        assert p1 == 1

    viewfn(rf.get("/?p1=1"))


def test_type_conversion_with_exception(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1: int | ValueError = param()):
        assert isinstance(p1, ValueError)

    viewfn(rf.get("/?p1=a"))


def test_type_conversion_float(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1: float = param()):
        assert p1 == 1.1
        # assert type(p1) == float
        assert isinstance(p1, float)

    viewfn(rf.get("/?p1=1.1"))


def test_type_conversion_bool(rf: RequestFactory):
    @inject_params()
    def viewfn(
        _request,
        p1: bool = param(),
        p2: bool = param(),
        p3: bool = param(),
    ):
        assert not p1
        assert not p2
        assert not p3

    viewfn(rf.get("/?p1=false&p2=False&p3"))


def test_type_conversion_list_unannotated(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1: list = param()):
        assert type(p1) == list
        assert "a" in p1
        assert "b" in p1

    viewfn(rf.get("/?p1=a&p1=b"))


def test_type_conversion_list_annotated(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1: list[int] = param()):
        assert type(p1) == list
        assert 1 in p1
        assert 2 in p1

    viewfn(rf.get("/?p1=1&p1=2"))


@pytest.mark.django_db
def test_type_conversion_model(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, user: AppUser = param()):
        assert user is not None

    app_user = AppUser.objects.create(username="testuser")
    viewfn(rf.get(f"/?user={app_user.id}"))


@pytest.mark.django_db
def test_type_conversion_model_wrong_id_object_does_not_exist_type(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, user: AppUser | ObjectDoesNotExist = param()):
        assert isinstance(user, ObjectDoesNotExist)

    viewfn(rf.get(f"/?user={uuid4()}"))


@pytest.mark.django_db
def test_type_conversion_model_wrong_id_object_does_not_exist__with_pktype(
    rf: RequestFactory,
):
    wrong_id = uuid4()

    @inject_params()
    def viewfn(_request, user: AppUser | ObjectDoesNotExistWithPk = param()):
        assert isinstance(user, ObjectDoesNotExistWithPk)
        assert user.pk == str(wrong_id)

    viewfn(rf.get(f"/?user={wrong_id}"))


@pytest.mark.django_db
def test_type_conversion_model_wrong_id_model_does_not_exist_type(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, user: AppUser | AppUser.DoesNotExist = param()):  # type: ignore
        assert isinstance(user, AppUser.DoesNotExist)

    viewfn(rf.get(f"/?user={uuid4()}"))


@pytest.mark.django_db
def test_type_conversion_model_with_optional(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, user: Optional[AppUser] = param()):
        assert user is not None

    app_user = AppUser.objects.create(username="testuser")
    viewfn(rf.get(f"/?user={app_user.id}"))


@pytest.mark.django_db
def test_type_conversion_model_with_optional_value_is_none(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, user: Optional[AppUser] = param()):
        assert user is None

    viewfn(rf.get("/"))


@pytest.mark.django_db
def test_type_conversion_model_with_union_none(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, user: AppUser | None = param()):
        assert user is not None

    app_user = AppUser.objects.create(username="testuser")
    viewfn(rf.get(f"/?user={app_user.id}"))


@pytest.mark.django_db
def test_type_conversion_model_with_union_none_value_is_none(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, user: AppUser | None = param()):
        assert user is None

    viewfn(rf.get("/"))


def test_post(rf: RequestFactory):
    @inject_params()
    def viewfn(
        _request,
        p1: str = param(methods=["POST"]),
        p2: str = param(methods=["POST"]),
    ):
        assert p1 == "a"
        assert p2 == "b"

    viewfn(rf.post("/", {"p1": "a", "p2": "b"}))


def test_patch(rf: RequestFactory):
    @inject_params()
    def viewfn(
        _request,
        p1: str = param(methods=["PATCH"], parse_form_urlencoded_body=True),
        p2: str = param(methods=["PATCH"], parse_form_urlencoded_body=True),
    ):
        assert p1 == "aaa"
        assert p2 == "bbb"

    viewfn(
        rf.patch(
            "/",
            urlencode({"p1": "aaa", "p2": "bbb"}),
            content_type="application/x-www-form-urlencoded",
        )
    )


def test_get_and_post_order(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1: str = param()):
        assert p1 == "a"

    viewfn(rf.post("/?p1=a", {"p1": "b"}))


def test_function_call_arg_overrides_param(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1: str = param()):
        assert p1 == "b"

    viewfn(rf.get("/?p1=a"), "b")


def test_function_call_kwarg_overrides_param(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1: str = param()):
        assert p1 == "b"

    viewfn(rf.get("/?p1=a"), p1="b")


def test_param_consume_true(rf: RequestFactory):
    @inject_params()
    def viewfn(request, p1: str = param()):
        assert p1 == "a"
        assert "p1" not in request.GET

    viewfn(rf.get("/?p1=a"))


def test_param_consume_false(rf: RequestFactory):
    @inject_params()
    def viewfn(request, p1: str = param(consume=False)):
        assert p1 == "a"
        assert "p1" in request.GET

    viewfn(rf.get("/?p1=a"))


def test_param_consume_get(rf: RequestFactory):
    @inject_params()
    def viewfn(request, p1: str = param()):
        assert p1 == "a"
        assert "p1" not in request.GET

    viewfn(rf.get("/?p1=a"))


def test_param_consume_post(rf: RequestFactory):
    @inject_params()
    def viewfn(request, p1: str = param(methods=["POST"])):
        assert p1 == "a"
        assert "p1" not in request.POST

    viewfn(rf.post("/", {"p1": "a"}))


def test_auto_default_value(rf: RequestFactory):
    @inject_params()
    def viewfn(_request, p1: str = param(default="a")):
        assert p1 == "a"

    untyped_viewfn = typing.cast(Any, viewfn)
    untyped_viewfn(rf.get("/"))


# def test_auto_param_false(rf: RequestFactory):
#     @inject_args(auto_param=False)
#     def viewfn(_request, p1: str):
#         assert p1 == "a"
#
#     untyped_viewfn = typing.cast(Any, viewfn)
#
#     def test():
#         untyped_viewfn(rf.get("/?p1=a"))
#
#     with pytest.raises(Exception, match="missing 1 required positional argument: 'p1'"):
#         test()


# def test_auto_param_true(rf: RequestFactory):
#     @inject_args(auto_param=True)
#     def viewfn(_request, p1: str):
#         assert p1 == "a"
#
#     untyped_viewfn = typing.cast(Any, viewfn)
#     untyped_viewfn(rf.get("/?p1=a"))


# def test_auto_param_get(rf: RequestFactory):
#     @inject_args(auto_param="get")
#     def viewfn(_request, p1: str):
#         assert p1 == "a"
#
#     untyped_viewfn = typing.cast(Any, viewfn)
#     untyped_viewfn(rf.get("/?p1=a"))


# def test_auto_param_get_does_not_receive_post_params(rf: RequestFactory):
#     @inject_args(auto_param="get")
#     def viewfn(_request, p1: str, p2="b"):
#         assert p1 == "a"
#         assert p2 == "b"
#
#     untyped_viewfn = typing.cast(Any, viewfn)
#     untyped_viewfn(rf.post("/?p1=a", {"p2": "x"}))


# def test_auto_param_post(rf: RequestFactory):
#     @inject_args(auto_param="post")
#     def viewfn(_request, p1: str):
#         assert p1 == "a"
#
#     untyped_viewfn = typing.cast(Any, viewfn)
#     untyped_viewfn(rf.post("/", {"p1": "a"}))


# def test_auto_param_post_does_not_receive_get_params(rf: RequestFactory):
#     @inject_args(auto_param="post")
#     def viewfn(_request, p1: str, p2="b"):
#         assert p1 == "a"
#         assert p2 == "b"
#
#     untyped_viewfn = typing.cast(Any, viewfn)
#     untyped_viewfn(rf.post("/p2=x", {"p1": "a"}))
