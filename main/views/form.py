from django import forms
from django.http import HttpRequest
from django.shortcuts import render
from django.urls import path, reverse

from dfv import element, handle_form


class FormPageForm(forms.Form):
    f1 = forms.CharField()
    f2 = forms.CharField()

    def is_valid(self):
        valid = super().is_valid()

        for field in self:
            if len(field.errors) > 0:
                field.field.widget.attrs["class"] = "invalid"

        return valid


def form_page(request):
    return render(
        request,
        "form/FormPage.html",
        {
            "form_element": form_element(request),
        },
    )


@element()
def form_element(
    request: HttpRequest,
    form: FormPageForm = handle_form(),
):
    if form.is_valid():
        print("form.cleaned_data", form.cleaned_data)

    return render(
        request,
        "form/FormElement.html",
        {
            "url": reverse("form_element"),
            "form": form,
        },
    )


urlpatterns = [
    path("", form_page, name="form_page"),
    path("form_element", form_element, name="form_element"),
]
