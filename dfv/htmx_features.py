import lxml.html
from django.http import HttpResponse

from dfv.utils import response_to_str


def swap_oob(
    response: HttpResponse,
    additional: HttpResponse | list[HttpResponse],
    hx_swap_oob_method="outerHTML",
) -> HttpResponse:
    if not isinstance(additional, list):
        additional = [additional]

    for a in additional:
        oob_content = response_to_str(a).strip()
        parsed: lxml.html.Element = lxml.html.fromstring(oob_content)
        id = parsed.attrib.get("id")
        if id is None:
            raise Exception(
                "The additional response does not contain exactly one element with an id attribute."
            )

        parsed.attrib["hx-swap-oob"] = f"{hx_swap_oob_method}:#{id}"
        response.content += lxml.html.tostring(parsed)
    return response
