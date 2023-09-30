from urllib.parse import urlencode

from django import forms
from django.http import HttpResponse
from django.test import RequestFactory

from dfv import view
from dfv.form import create_form, is_valid_submit


class TwoFieldForm(forms.Form):
    p1 = forms.CharField()
    p2 = forms.CharField()


def test_form_get(rf: RequestFactory):
    @view()
    def viewfn(request):
        form = create_form(request, TwoFieldForm)
        return HttpResponse(form)

    req = rf.get("/view")
    res = viewfn(req)
    assert res.content == (
        b"""<input type="text" name="p1" required id="id_p1">"""
        b"""<input type="text" name="p2" required id="id_p2">"""
    )


def test_form_patch(rf: RequestFactory):
    form_ref = []

    @view()
    def viewfn(request):
        fi = create_form(request, TwoFieldForm)
        form_ref.append(fi)
        return HttpResponse()

    req = rf.patch(
        "/view",
        urlencode({"p1": "a"}),
        content_type="application/x-www-form-urlencoded",
    )
    viewfn(req)
    form = form_ref[0]
    assert form is not None
    assert form.initial["p1"] == "a"


def test_form_patch_initial(rf: RequestFactory):
    form_ref = []

    @view()
    def viewfn(request):
        fi = create_form(request, TwoFieldForm, initial={"p2": "b"})
        form_ref.append(fi)
        return HttpResponse()

    req = rf.patch(
        "/view",
        urlencode({"p1": "a"}),
        content_type="application/x-www-form-urlencoded",
    )
    viewfn(req)
    form = form_ref[0]
    assert form is not None
    assert form.initial["p1"] == "a"
    assert form.initial["p2"] == "b"


def test_form_post(rf: RequestFactory):
    cleaned_data = {}

    @view()
    def viewfn(request):
        form = create_form(request, TwoFieldForm)
        assert is_valid_submit(request, form)
        cleaned_data.update(form.cleaned_data)
        return HttpResponse()

    req = rf.post("/view", {"p1": "a", "p2": "b"})
    viewfn(req)
    assert cleaned_data["p1"] == "a"
    assert cleaned_data["p2"] == "b"


# def test_error_missing_form_type():
#     def test():
#         @view()
#         def viewfn(_request, form=handle_form()):
#             return HttpResponse(form)
#
#     with pytest.raises(
#         Exception,
#         match=r"argument type for handle_form\(\) must be a subclass of django.forms.BaseForm",
#     ):
#         test()


# def test_error_wrong_form_type():
#     def test():
#         @view()
#         def viewfn(_request, _form: str = handle_form()):
#             return HttpResponse("")
#
#     with pytest.raises(
#         Exception,
#         match=r"argument type for handle_form\(\) must be a subclass of django.forms.BaseForm",
#     ):
#         test()


# def test_form_explicit():
#     @view()
#     def viewfn(_request, form: TwoFieldForm = handle_form()):
#         assert type(form) == TwoFieldForm
#         return HttpResponse("")
#
#     viewfn(create_resolved_request(viewfn, "POST", {"p1": "a", "p2": "b"}))


# def test_form_implicit():
#     @view()
#     def viewfn(_request, form: TwoFieldForm):
#         assert type(form) == TwoFieldForm
#         return HttpResponse("")
#
#     typing.cast(Any, viewfn)(
#         create_resolved_request(viewfn, "POST", {"p1": "a", "p2": "b"})
#     )


# def test_form_get():
#     @view()
#     def viewfn(_request, form: TwoFieldForm = handle_form()):
#         assert not form.is_bound
#         assert not form.is_valid()
#         return HttpResponse("")
#
#     viewfn(create_resolved_request(viewfn, "GET", {"p1": "a", "p2": "b"}))


# def test_form_post():
#     @view()
#     def viewfn(_request, form: TwoFieldForm = handle_form()):
#         assert form.is_bound
#         assert form.is_valid()
#         assert form.cleaned_data["p1"] == "a"
#         assert form.cleaned_data["p2"] == "b"
#         return HttpResponse("")
#
#     viewfn(create_resolved_request(viewfn, "POST", {"p1": "a", "p2": "b"}))


# def test_initial():
#     @inject_args(auto_param=True)
#     def kwargs_factory(_request: HttpRequest, p1: str, p2: str):
#         return {
#             "initial": {"p1": f"initial {p1}", "p2": f"initial {p2}"},
#         }
#
#     @view()
#     def viewfn(
#         _request, form: TwoFieldForm = handle_form(kwargs_factory=kwargs_factory)
#     ):
#         assert form.initial["p1"] == "initial ia"
#         assert form.initial["p2"] == "initial ib"
#         return HttpResponse("")
#
#     viewfn(create_resolved_request(viewfn, "GET", {"p1": "ia", "p2": "ib"}))


# def test_form_patch(rf: RequestFactory):
#     @view()
#     def viewfn(_request, form: TwoFieldForm = handle_form()):
#         assert form.is_bound
#         assert not form.is_valid()
#         return HttpResponse("")
#
#     urlpatterns = (path("view/", viewfn, name="a view"),)
#     resolved = resolve("/view/", urlconf=urlpatterns)
#     request = rf.patch(
#         "/",
#         json.dumps({"p1": "", "p2": "b"}),
#         "application/json",
#         headers={"X-DFV-Validate-Field": "p1"},
#     )
#     request.resolver_match = resolved
#
#     response = viewfn(request)
#     assert response.status_code == 200
#     assert response["Content-Type"] == "application/json"
#     body = json.loads(response.content)
#     assert body["name"] == "p1"
#     field_p1 = body["fields"]["p1"]
#     assert not field_p1["valid"]
#     field_p2 = body["fields"]["p2"]
#     assert field_p2["valid"]
