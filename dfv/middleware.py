from django.http import HttpResponse

from dfv.response_handler import process_response
from dfv.utils import response_to_str


class DFVMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request) -> HttpResponse:
        response: HttpResponse = self.get_response(request)
        if (
            response is not None
            and not response.streaming
            and response["Content-Type"].startswith("text/html")
        ):
            response = process_response(request, response)
            content = response_to_str(response)
            bcontent = bytes(content, "UTF-8")
            dfv_swap_oob = getattr(response, "_dfv_swap_oob", [])
            for oob in dfv_swap_oob:
                bcontent += oob
            response.content = bcontent

        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        pass
