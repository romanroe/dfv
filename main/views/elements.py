from datetime import datetime

from django.http import HttpRequest
from django.shortcuts import render

from dfv import element, param, view
from dfv.htmx import swap_oob
from dfv.route import create_route


@view()
def level1_page(request: HttpRequest):
    return render(
        request,
        "elements/Level1Page.html",
        {
            "timestamp": datetime.now().microsecond,
            "level2_element": level2_element(request, source="level1_page"),
        },
    )


@element()
def level2_element(request: HttpRequest, source="level2"):
    return render(
        request,
        "elements/Level2Element.html",
        {
            "timestamp": datetime.now().microsecond,
            "source": source,
            "level3a_element": level3a_element(request, source=source),
            "level3b_element": level3b_element(request, source=source),
        },
    )


@element()
def level3a_element(
    request: HttpRequest,
    source="level3a",
    action=param(""),
):
    response = render(
        request,
        "elements/Level3AElement.html",
        {
            "timestamp": datetime.now().microsecond,
            "source": source,
        },
    )

    match action:
        case "2":
            return swap_oob(response, level2_element(request, source="level3a_element"))
        case "3a_3b":
            return swap_oob(
                response, level3b_element(request, source="level3a_element")
            )
        case "replace":
            return level3b_element(request, "replace")

    return response


@element("l3b", tag="span")
def level3b_element(request: HttpRequest, source=""):
    return render(
        request,
        "elements/Level3BElement.html",
        {"timestamp": datetime.now().microsecond, "source": source},
    )


urlpatterns = [
    create_route(level1_page, ""),
    create_route(level3a_element),
]
