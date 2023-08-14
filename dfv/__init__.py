import dataclasses
import functools
import inspect
import json
import typing
import uuid
from types import NoneType
from typing import Any, Callable, Literal, Optional, TypeVar

import lxml.html
import wrapt
from django import forms
from django.contrib.auth import decorators as auth_decorators
from django.http import HttpRequest, HttpResponse, JsonResponse, QueryDict
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe, SafeString

# P = ParamSpec("P")
T = TypeVar("T")

VIEW_FN = TypeVar("VIEW_FN", bound=Callable[..., HttpResponse])


################################################################################
### view
################################################################################


@typing.overload
def get_view_fn_call_stack_from_request(request: HttpRequest) -> list[Callable]:
    ...


@typing.overload
def get_view_fn_call_stack_from_request(
    request: HttpRequest, create: bool
) -> Optional[list[Callable]]:
    ...


def get_view_fn_call_stack_from_request(
    request: HttpRequest, create=True
) -> Optional[list[Callable]]:
    call_stack = getattr(request, "__dfv_view_fn_call_stack", None)
    call_stack = [] if call_stack is None and create else call_stack
    setattr(request, "__dfv_view_fn_call_stack", call_stack)
    return call_stack


class ViewResponse(wrapt.ObjectProxy):
    def __str__(self):
        return response_to_str(self)


def view(
    *,
    decorators: Optional[list[Callable]] = None,
    login_required=False,
    handle_args=True,
) -> Callable[[VIEW_FN], VIEW_FN]:
    if decorators is None:
        decorators = []

    if login_required:
        decorators = [auth_decorators.login_required(), *decorators]

    def decorator(fn: VIEW_FN) -> VIEW_FN:
        if handle_args:
            fn = _inject_args()(fn)

        if decorators is not None:
            for d in reversed(decorators):
                fn = d(fn)

        @functools.wraps(fn)
        def inner(*args, **kwargs) -> HttpResponse:
            view_request: HttpRequest = args[0]
            stack = get_view_fn_call_stack_from_request(view_request)
            try:
                stack.append(fn)
                result = fn(*args, **kwargs)
                return (
                    ViewResponse(result)
                    if not isinstance(result, ViewResponse)
                    else result
                )
            finally:
                stack.pop()

        return typing.cast(VIEW_FN, inner)

    return decorator


def is_view_fn_request_target(request: HttpRequest):
    stack = get_view_fn_call_stack_from_request(request, create=False)
    if stack is None or len(stack) == 0:
        raise Exception("This function can only be called from within a DFV view.")
    if len(stack) != 1:
        return False

    called_view: Callable = stack[0]
    return called_view.__qualname__ == request.resolver_match.func.__qualname__


def is_head(request: HttpRequest, ignore_resolved_view=True):
    return (
        ignore_resolved_view or is_view_fn_request_target(request)
    ) and request.method == "HEAD"


def is_get(request: HttpRequest, ignore_resolved_view=True):
    return (
        ignore_resolved_view or is_view_fn_request_target(request)
    ) and request.method == "GET"


def is_post(request: HttpRequest, ignore_resolved_view=False):
    return (
        ignore_resolved_view or is_view_fn_request_target(request)
    ) and request.method == "POST"


def is_put(request: HttpRequest, ignore_resolved_view=False):
    return (
        ignore_resolved_view or is_view_fn_request_target(request)
    ) and request.method == "PUT"


def is_patch(request: HttpRequest, ignore_resolved_view=False):
    return (
        ignore_resolved_view or is_view_fn_request_target(request)
    ) and request.method == "PATCH"


def is_delete(request: HttpRequest, ignore_resolved_view=False):
    return (
        ignore_resolved_view or is_view_fn_request_target(request)
    ) and request.method == "DELETE"


################################################################################
### element
################################################################################


class ElementResponse(ViewResponse):
    @staticmethod
    def empty() -> HttpResponse:
        return ElementResponse(HttpResponse(), None, no_element_wrap=True)

    def __init__(
        self,
        response: HttpResponse,
        element_id: Optional[str],
        tag="div",
        hx_target="this",
        hx_swap="outerHTML",
        classes: Optional[str] = None,
        no_element_wrap=False,
    ):
        if not no_element_wrap:
            attr_id = f"id='{element_id}'" if element_id is not None else ""
            attr_hx_target = f"hx-target='{hx_target}'" if hx_target else ""
            attr_hx_swap = f"hx-swap='{hx_swap}'" if hx_swap else ""
            attr_classes = f"class='{classes}'" if classes else ""
            new_content = (
                f"""<{tag} {attr_id} {attr_hx_target} {attr_hx_swap} {attr_classes}>"""
                f"""{response_to_str(response)}"""
                f"""</{tag}>"""
            )
            response.content = bytes(new_content, "UTF-8")

        super().__init__(response)

    def __str__(self):
        return response_to_str(self)


def response_to_str(response: HttpResponse | TemplateResponse) -> SafeString:
    if isinstance(response, TemplateResponse):
        response = response.render()

    return mark_safe(str(response.content, "utf-8"))


# noinspection PyShadowingNames
def element(
    element_id: Optional[str] = None,
    *,
    tag="div",
    hx_target="this",
    hx_swap="outerHTML",
    classes: Optional[str] = None,
    handle_args=True,
    decorators: Optional[list[Callable]] = None,
    login_required=False,
) -> Callable[[VIEW_FN], VIEW_FN]:
    def decorator(f: VIEW_FN) -> VIEW_FN:
        id = element_id if isinstance(element_id, str) else f.__name__
        f = view(
            handle_args=handle_args,
            decorators=decorators,
            login_required=login_required,
        )(f)

        @functools.wraps(f)
        def inner(*args, **kwargs) -> HttpResponse:
            response = f(*args, **kwargs)
            if not response["Content-Type"].startswith("text/html"):
                return response

            if isinstance(response, ElementResponse):
                return response

            return ElementResponse(
                response,
                element_id=id,
                tag=tag,
                hx_target=hx_target,
                hx_swap=hx_swap,
                classes=classes,
            )

        return typing.cast(VIEW_FN, inner)

    return decorator


def swap_oob(
    response: HttpResponse, additional: HttpResponse, hx_swap_oob_method="outerHTML"
) -> HttpResponse:
    oob_content = response_to_str(additional).strip()
    parsed: lxml.html.Element = lxml.html.fromstring(oob_content)
    id = parsed.attrib.get("id")
    if id is None:
        raise Exception(
            "The additional response does not contain exactly one element with an id attribute."
        )

    parsed.attrib["hx-swap-oob"] = f"{hx_swap_oob_method}:#{id}"
    response.content += lxml.html.tostring(parsed)
    return response


################################################################################
### inject_args
################################################################################


def inject_args(
    *,
    auto_param: bool | Literal["get", "post"] = False,
    auto_form: Optional[bool | str] = True,
) -> Callable[[VIEW_FN], VIEW_FN]:
    def decorator(fn: VIEW_FN) -> VIEW_FN:
        parameters: list[inspect.Parameter] = list(
            inspect.signature(fn).parameters.values()
        )
        injected_params = _extract_injected_params(
            fn, parameters, auto_param, auto_form
        )
        arg_names = [p.name for p in parameters]

        @functools.wraps(fn)
        def inner(*args, **kwargs) -> HttpResponse:
            supplied_args = arg_names[: len(args)]
            for name, ip in injected_params.items():
                if name not in kwargs and name not in supplied_args:
                    kwargs[name] = ip.get_value(args, kwargs)
                    replace_response = ip.replace_response(
                        _get_request_from_args(typing.cast(Any, args)), kwargs[name]
                    )
                    if replace_response is not None:
                        return replace_response

            return fn(*args, **kwargs)

        return typing.cast(VIEW_FN, inner)

    return decorator


# alias, to allow parameters to be named handle_args
_inject_args = inject_args


@dataclasses.dataclass
class InjectedParam:
    name: str = dataclasses.field(init=False)
    target_type: type = dataclasses.field(init=False)
    view_fn: Callable[[Any], Any] = dataclasses.field(init=False)

    def check(self):
        pass

    def get_value(self, args: Any, kwargs: dict[str, Any]) -> Any:
        pass

    def replace_response(
        self, request: HttpRequest, value: Any
    ) -> Optional[HttpResponse]:
        pass


def _setup_injected_param(
    view_fn: Callable[[Any], Any],
    ip: InjectedParam,
    name: str,
    parameter: inspect.Parameter,
):
    ip.name = name
    ip.target_type = (
        parameter.annotation
        if parameter.annotation is not inspect.Signature.empty
        else type(parameter.default)
        if parameter.default is not inspect.Parameter.empty
        and not isinstance(parameter.default, InjectedParam)
        else type(parameter.default.default)
        if isinstance(parameter.default, InjectedParamQuery)
        and parameter.default.default is not None
        else str
    )
    ip.view_fn = view_fn
    ip.check()
    return ip


def _extract_injected_params(
    view_fn: Callable[[Any], Any],
    parameters: list[inspect.Parameter],
    auto_param: bool | Literal["get"] | Literal["post"],
    auto_form: Optional[bool | str] = True,
) -> dict[str, InjectedParam]:
    """
    Extracts all injected parameters from the given list of function arguments.
    """
    result: dict[str, InjectedParam] = {}

    # skip first request parameter
    parameters = parameters[1:]

    found_form_arg = False
    for arg in parameters:
        if isinstance(arg.default, InjectedParam):
            ip: InjectedParam = arg.default
            result[ip.name] = _setup_injected_param(view_fn, ip, arg.name, arg)

        # elif arg.default == inspect.Parameter.empty:
        else:
            default_value = (
                arg.default if arg.default != inspect.Parameter.empty else None
            )
            # handle form
            if (
                auto_form
                and isinstance(arg.annotation, type)
                and issubclass(arg.annotation, forms.BaseForm)
            ):
                if found_form_arg:
                    raise Exception(
                        "You can only have one Form argument in a view function."
                    )
                found_form_arg = True
                result[arg.name] = _setup_injected_param(
                    view_fn, handle_form(), arg.name, arg
                )
            # from here, handle get and post params
            elif auto_param is True:
                result[arg.name] = _setup_injected_param(
                    view_fn, InjectedParamQuery(default=default_value), arg.name, arg
                )
            elif auto_param == "get":
                result[arg.name] = _setup_injected_param(
                    view_fn, InjectedParamQueryGet(default=default_value), arg.name, arg
                )
            elif auto_param == "post":
                result[arg.name] = _setup_injected_param(
                    view_fn,
                    InjectedParamQueryPost(default=default_value),
                    arg.name,
                    arg,
                )

    return result


################################################################################
### request params to args
################################################################################


@dataclasses.dataclass
class InjectedParamQuery(InjectedParam):
    query_param_name: Optional[str] = dataclasses.field(default=None)
    default: Any = dataclasses.field(default=None)
    consume: bool = dataclasses.field(default=True)

    def check(self):
        if self.query_param_name is None:
            self.query_param_name = self.name

    def _create_lookup_dict(self, request: HttpRequest):
        getqd = typing.cast(QueryDict, request.GET)
        getd = {name: getqd.getlist(name) for name in getqd}
        postqd = typing.cast(QueryDict, request.POST)
        postd = {name: postqd.getlist(name) for name in postqd}
        return postd | getd

    def _consume_param(self, request: HttpRequest):
        if self.query_param_name in request.GET:
            request.GET = querydict_key_removed(
                typing.cast(Any, request.GET), self.query_param_name
            )
        elif self.query_param_name in request.POST:
            request.POST = querydict_key_removed(
                typing.cast(Any, request.POST), self.query_param_name
            )

    def get_value(self, args: Any, kwargs: dict[str, Any]):
        request = _get_request_from_args(args)
        lookup_dict = self._create_lookup_dict(request)
        values = lookup_dict.get(self.query_param_name, None)

        if values is None:
            if self.default is not None:
                values = [self.default]
            elif issubclass(NoneType, self.target_type):
                return None
            else:
                raise Exception(
                    f"No value found for request parameter '{self.query_param_name}'"
                )

        if self.consume:
            self._consume_param(request)

        return _convert_value_to_type(values, self.target_type)


@dataclasses.dataclass
class InjectedParamQueryGet(InjectedParamQuery):
    def _create_lookup_dict(self, request: HttpRequest):
        qd = typing.cast(QueryDict, request.GET)
        return {name: qd.getlist(name) for name in qd}

    def _consume_param(self, request: HttpRequest):
        if self.query_param_name in request.GET:
            request.GET = querydict_key_removed(
                typing.cast(Any, request.GET), self.query_param_name
            )


@dataclasses.dataclass
class InjectedParamQueryPost(InjectedParamQuery):
    def _create_lookup_dict(self, request: HttpRequest):
        qd = typing.cast(QueryDict, request.POST)
        return {name: qd.getlist(name) for name in qd}

    def _consume_param(self, request: HttpRequest):
        if self.query_param_name in request.POST:
            request.POST = querydict_key_removed(
                typing.cast(Any, request.POST), self.query_param_name
            )


def param_get(default=None, consume=True) -> Any:
    return InjectedParamQueryGet(default=default, consume=consume)


def param_post(default=None, consume=True) -> Any:
    return InjectedParamQueryPost(default=default, consume=consume)


def param(default: T = typing.cast(Any, None), consume=True) -> T:
    return typing.cast(T, InjectedParamQuery(default=default, consume=consume))


def _convert_value_to_type(values: list[typing.Any], target_type: type):
    # List type
    if typing.get_origin(target_type) == list:
        list_type = typing.get_args(target_type)[0]
        return [_convert_value_to_type([v], list_type) for v in values]

    if target_type == list:
        return [_convert_value_to_type([v], str) for v in values]

    # Scalar types
    value = values[0]

    if value is None:
        pass  # trigger ValueError
    elif isinstance(value, target_type):
        return value  # nothing to do
    elif issubclass(str, target_type):
        return str(value)
    elif issubclass(int, target_type):
        return int(value)
    elif issubclass(float, target_type):
        return float(value)
    elif issubclass(bool, target_type):
        return False if value in (False, "", "false", "False") else True
    elif issubclass(uuid.UUID, target_type):
        return uuid.UUID(value)

    raise ValueError(f"Unsupported type: {target_type} for value: {value}")


################################################################################
### form
################################################################################


@dataclasses.dataclass
class InjectedParamForm(InjectedParam):
    initial: Optional[Callable[..., Any]] = dataclasses.field(default=None)

    def check(self):
        if not issubclass(self.target_type, forms.BaseForm):
            raise Exception(
                f"argument type for handle_form() must be a subclass of django.forms.BaseForm, got {self.target_type}"
            )

    def get_value(self, args: Any, kwargs: dict[str, Any]):
        request = _get_request_from_args(args)
        form_kwargs = {}
        if self.initial is not None:
            form_kwargs["initial"] = self.initial(request)

        if is_post(request):
            form = self.target_type(
                data=request.POST, files=request.FILES, **form_kwargs
            )
        elif request.content_type == "application/json":
            new_post_dict = typing.cast(QueryDict, request.POST).copy()
            new_post_dict.update(json.loads(request.body))
            form = self.target_type(data=new_post_dict, **form_kwargs)
        else:
            form = self.target_type(**form_kwargs)
        return form

    def replace_response(
        self, request: HttpRequest, value: forms.Form
    ) -> Optional[HttpResponse]:
        if is_patch(request) and request.content_type == "application/json":
            validate_field = request.headers.get("X-DFV-Validate-Field")
            value.is_valid()
            fields = {}
            for bound_field in value:
                widget = bound_field.field.widget
                fields[bound_field.name] = {
                    "valid": len(bound_field.errors) == 0,
                    "errors": str(value[bound_field.name].errors),
                    "attrs": widget.attrs,
                }

            return JsonResponse(
                {
                    "name": validate_field,
                    "fields": fields,
                    "non_field_errors": str(value.non_field_errors()),
                    "form_valid": value.is_valid(),
                }
            )

        return None


def handle_form(*, initial: Optional[Callable[..., Any]] = None) -> Any:
    return InjectedParamForm(initial=initial)


################################################################################
### utils
################################################################################


def querydict_key_removed(querydict: dict, key) -> QueryDict:
    temp = QueryDict(mutable=True)
    temp.update(querydict)
    del temp[key]
    return temp


def _get_request_from_args(args: list[Any]) -> HttpRequest:
    return args[0]
