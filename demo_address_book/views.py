from uuid import UUID

from django import forms
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import path
from icecream import ic

from demo_address_book.models import Person
from dfv import element, param, view
from dfv.form import create_form, is_valid_submit
from dfv.route import create_path, reverse_view


@view()
def address_book_page(
    request: HttpRequest,
    person_id: UUID | None = param(),
):
    return render(
        request,
        "demo_address_book/address_book_page.html",
        {
            "list_element": list_element(request, person_id=person_id),
            "detail_element": detail_element(
                request, person_id=str(person_id) if person_id is not None else "new"
            ),
        },
    )


@element()
def list_element(
    request: HttpRequest,
    action=param("", methods=["POST"]),
    filter_text: str = param(""),
    page: int = param(0),
    person_id: UUID | None = param(methods=["POST"]),
):
    # ic(action, person_id)
    # ic(reverse_view(detail_element, args=["123"]))

    persons = Person.objects.all()
    filter_text = filter_text.strip()
    if filter_text:
        persons = persons.filter(
            Q(first_name__icontains=filter_text) | Q(last_name__icontains=filter_text)
        )
    persons = persons.order_by("first_name", "last_name")

    page_size = 30
    persons = persons[page * page_size : ((page + 1) * page_size) + 1]

    return render(
        request,
        "demo_address_book/list_element.html",
        {
            "url": reverse_view(list_element),
            "view": list_element,
            "page": page,
            "has_more_pages": len(persons) > page_size,
            "filter_text": filter_text,
            "persons": persons,
            "person_id": person_id,
            "detail_element": detail_element,
        },
    )


# @view()
# def action_open_person(request: HttpRequest, person_id: UUID):
#     hook_swap_oob(
#         request,
#         [
#             list_element(request, person_id=person_id),
#             detail_element(request, person_id=str(person_id)),
#         ],
#     )
#     return push_url(
#         reswap(HttpResponse(), "none"),
#         f"""{reverse("address-book-page")}?person_id={person_id}""",
#     )


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ["first_name", "last_name"]


@element()
def detail_element(
    request: HttpRequest,
    person_id: str,
):
    person = Person.objects.get(id=person_id) if person_id != "new" else None

    form = create_form(
        request, PersonForm, instance=person, initial={"first_name": "aaa"}
    )

    # ic(form.data)
    # ic(form["first_name"].value())
    # ic(form.initial)

    if is_valid_submit(request, form):
        form.save()
        # return action_open_person(request, person_id=person.id)

    return render(
        request,
        "demo_address_book/detail_element.html",
        {
            # "url": reverse_view(detail_element, person_id=person_id),
            "target": """aaa""",
            "person": person,
            "form": form,
        },
    )


@view()
def foo(request, foo=param(methods=["__all__"])):
    ic(foo)
    return HttpResponse("foo")


urlpatterns = [
    path("foo", foo, name="foo"),
    path("", address_book_page, name="address-book-page"),
    create_path(list_element),
    create_path(detail_element)
    ###
    ###
    # path(
    #     "action_open_person/<uuid:person_id>",
    #     action_open_person,
    #     name="address-book-page-action-open-person",
    # ),
    # path("detail/", detail_element, name="address-book-page-detail"),
    # path("detail/<uuid:person_id>", detail_element, name="address-book-page-detail"),
]
