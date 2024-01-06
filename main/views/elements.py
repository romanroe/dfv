from datetime import datetime

from django.http import HttpRequest
from django.shortcuts import render

from dfv import element, is_post, view
from dfv.element import body_response
from dfv.htmx import swap_oob
from dfv.route import create_path


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
    # action=param("", consume=False),
):
    response = render(
        request,
        "elements/Level3AElement.html",
        {
            "timestamp": datetime.now().microsecond,
            "source": source,
            "self": level3a_element,
        },
    )

    # actions = Actions(request)
    #
    # @actions.add
    # def action_page(_):
    #     return body_response(level1_page(request))
    #
    # if actions.matched():
    #     return actions.value

    match is_post(request), request.POST:
        case True, {"action_page": _}:
            return body_response(level1_page(request))
        case True, {"action": "2"}:
            return swap_oob(response, level2_element(request, source="level3a_element"))
        case True, {"action": "3a_3b"}:
            return swap_oob(
                response, level3b_element(request, source="level3a_element")
            )
        case True, {"action": "replace"}:
            return level3b_element(request, "replace")

    # if is_post(request):
    #     match action:
    # case "page":
    #     return body_response(level1_page(request))
    # case "2":
    #     return swap_oob(
    #         response, level2_element(request, source="level3a_element")
    #     )
    # case "3a_3b":
    #     return swap_oob(
    #         response, level3b_element(request, source="level3a_element")
    #     )
    # case "replace":
    #     return level3b_element(request, "replace")

    return response


@element("l3b", tag="span")
def level3b_element(request: HttpRequest, source=""):
    return render(
        request,
        "elements/Level3BElement.html",
        {"timestamp": datetime.now().microsecond, "source": source},
    )


urlpatterns = [
    create_path(level1_page, url=""),
    create_path(level3a_element),
]
