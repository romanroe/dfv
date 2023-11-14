from uuid import UUID

from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import path, reverse
from django_htmx.http import reswap
from icecream import ic

from demo_address_book.models import Person
from dfv import element, param, view
from dfv.response_handler import hook_swap_oob


@view()
def address_book_page(request: HttpRequest):
    return render(
        request,
        "demo_address_book/address_book_page.html",
        {
            "list_element": list_element(request),
        },
    )


@element()
def list_element(
    request: HttpRequest,
    filter_text: str = param("", consume=False),
    active: UUID | None = None,
):
    ic("list", request.GET)
    persons = Person.objects.all()
    if filter_text:
        persons = persons.filter(
            Q(first_name__icontains=filter_text) | Q(last_name__icontains=filter_text)
        )

    return render(
        request,
        "demo_address_book/list_element.html",
        {
            "url": reverse("address-book-page-list"),
            "filter_text": filter_text,
            "persons": persons,
            "active": active,
        },
    )


@view()
def action_open_person(
    request: HttpRequest,
    person_id: UUID,
):
    ic("action-open", request.GET)
    hook_swap_oob(
        request,
        [
            list_element(request, active=person_id),
            detail_element(request, person_id),
        ],
    )
    return reswap(HttpResponse(), "none")


@element()
def detail_element(
    request: HttpRequest,
    person_id: UUID,
):
    ic("detail", person_id, request.GET)
    person = Person.objects.get(id=person_id)
    return render(
        request,
        "demo_address_book/detail_element.html",
        {
            "person": person,
        },
    )


urlpatterns = [
    path("", address_book_page, name="address-book-page"),
    path("list", list_element, name="address-book-page-list"),
    path(
        "action_open_person/<uuid:person_id>",
        action_open_person,
        name="address-book-page-action-open-person",
    ),
    path("detail/<uuid:person_id>", detail_element, name="address-book-page-detail"),
]
