import dataclasses
import functools
import inspect
import typing
import uuid
from dataclasses import dataclass
from types import NoneType, UnionType
from typing import (
    Any,
    Callable,
    cast,
    get_args,
    get_origin,
    Literal,
    Optional,
    Type,
    TypeVar,
)

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.http import HttpRequest, HttpResponse, QueryDict

from dfv.utils import _get_request_from_args, querydict_key_removed

VIEW_FN = TypeVar("VIEW_FN", bound=Callable[..., HttpResponse])


def inject_args(
    *,
    auto_param: bool | Literal["get", "post"] = False,
    # auto_form: Optional[bool | str] = True,
) -> Callable[[VIEW_FN], VIEW_FN]:
    def decorator(fn: VIEW_FN) -> VIEW_FN:
        parameters: list[inspect.Parameter] = list(
            inspect.signature(fn).parameters.values()
        )
        injected_params = _extract_injected_params(
            fn, parameters, auto_param  # , auto_form
        )
        arg_names = [p.name for p in parameters]

        @functools.wraps(fn)
        def inner(*args, **kwargs) -> HttpResponse:
            supplied_args = arg_names[: len(args)]
            for name, ip in injected_params.items():
                if name not in kwargs and name not in supplied_args:
                    kwargs[name] = ip.get_value(args, kwargs)
                    replace_response = ip.replace_response(
                        _get_request_from_args(cast(Any, args)), kwargs[name]
                    )
                    if replace_response is not None:
                        return replace_response

            return fn(*args, **kwargs)

        return cast(VIEW_FN, inner)

    return decorator


# alias, to allow parameters to be named handle_args
# _inject_args = inject_args


@dataclass
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
    # auto_form: Optional[bool | str] = True,
) -> dict[str, InjectedParam]:
    """
    Extracts all injected parameters from the given list of function arguments.
    """
    result: dict[str, InjectedParam] = {}

    # skip first request parameter
    parameters = parameters[1:]

    # found_form_arg = False
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
            # if (
            #     auto_form
            #     and isinstance(arg.annotation, type)
            #     and issubclass(arg.annotation, forms.BaseForm)
            # ):
            #     if found_form_arg:
            #         raise Exception(
            #             "You can only have one Form argument in a view function."
            #         )
            #     found_form_arg = True
            #     result[arg.name] = _setup_injected_param(
            #         view_fn, handle_form(), arg.name, arg
            #     )
            # from here, handle get and post params
            if auto_param is True:
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
        getqd = cast(QueryDict, request.GET)
        getd = {name: getqd.getlist(name) for name in getqd}
        postqd = cast(QueryDict, request.POST)
        postd = {name: postqd.getlist(name) for name in postqd}

        formqd = QueryDict(mutable=True)
        if request.content_type == "application/x-www-form-urlencoded":
            formqd.update(
                QueryDict(request.body, mutable=True, encoding=request.encoding)
            )
        return postd | getd | formqd

    def _consume_param(self, request: HttpRequest):
        if self.query_param_name in request.GET:
            request.GET = querydict_key_removed(
                cast(Any, request.GET), self.query_param_name
            )
        elif self.query_param_name in request.POST:
            request.POST = querydict_key_removed(
                cast(Any, request.POST), self.query_param_name
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
        qd = cast(QueryDict, request.GET)
        return {name: qd.getlist(name) for name in qd}

    def _consume_param(self, request: HttpRequest):
        if self.query_param_name in request.GET:
            request.GET = querydict_key_removed(
                cast(Any, request.GET), self.query_param_name
            )


@dataclasses.dataclass
class InjectedParamQueryPost(InjectedParamQuery):
    def _create_lookup_dict(self, request: HttpRequest):
        qd = cast(QueryDict, request.POST)
        return {name: qd.getlist(name) for name in qd}

    def _consume_param(self, request: HttpRequest):
        if self.query_param_name in request.POST:
            request.POST = querydict_key_removed(
                cast(Any, request.POST), self.query_param_name
            )


def param_get(default=None, consume=True) -> Any:
    return InjectedParamQueryGet(default=default, consume=consume)


def param_post(default=None, consume=True) -> Any:
    return InjectedParamQueryPost(default=default, consume=consume)


T = TypeVar("T")


def param(default: T = cast(Any, None), consume=True) -> T:
    return cast(T, InjectedParamQuery(default=default, consume=consume))


def check_and_return_model_type(target_type: Any) -> Type[models.Model] | None:
    if get_origin(target_type) is typing.Union or isinstance(target_type, UnionType):
        # union type
        for t in get_args(target_type):
            if issubclass(t, models.Model):
                return cast(Type[models.Model], t)
    elif issubclass(target_type, models.Model):
        # no union type
        return cast(Type[models.Model], target_type)

    return None


class ObjectDoesNotExistWithPk(ObjectDoesNotExist):
    pk: Any

    def __init__(self, pk: Any):
        super().__init__(f"Object with pk {pk} does not exist")
        self.pk = pk


def _convert_value_to_type(values: list[Any], target_type: type):
    # List type
    if get_origin(target_type) == list:
        list_type = get_args(target_type)[0]
        return [_convert_value_to_type([v], list_type) for v in values]

    if target_type == list:
        return [_convert_value_to_type([v], str) for v in values]

    # Scalar types
    value = values[0]

    try:
        if value is None:
            pass  # trigger ValueError
        elif model_type := check_and_return_model_type(target_type):
            try:
                return model_type.objects.get(pk=value)
            except model_type.DoesNotExist as e:
                if issubclass(ObjectDoesNotExistWithPk, target_type):
                    raise ObjectDoesNotExistWithPk(value)
                raise e
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
    except Exception as error:
        if isinstance(error, target_type):
            return error
        raise error

    raise ValueError(f"Unsupported type: {target_type} for value: {value}")


# @dataclasses.dataclass
# class InjectedParamForm(InjectedParam):
#     kwargs_factory: Optional[Callable[..., dict[str, Any]]] = dataclasses.field(
#         default=None
#     )
#
#     def check(self):
#         if not issubclass(self.target_type, forms.BaseForm):
#             raise Exception(
#                 f"argument type for handle_form() must be a subclass of django.forms.BaseForm, got {self.target_type}"
#             )
#
#     def get_value(self, args: Any, kwargs: dict[str, Any]):
#         request = _get_request_from_args(args)
#         form_kwargs = (
#             self.kwargs_factory(request) if self.kwargs_factory is not None else {}
#         )
#
#         if is_post(request):
#             form = self.target_type(
#                 data=request.POST, files=request.FILES, **form_kwargs
#             )
#         elif request.content_type == "application/json":
#             new_post_dict = cast(QueryDict, request.POST).copy()
#             new_post_dict.update(json.loads(request.body))
#             form = self.target_type(data=new_post_dict, **form_kwargs)
#         else:
#             form = self.target_type(**form_kwargs)
#         return form
#
#     def replace_response(
#         self, request: HttpRequest, value: forms.Form
#     ) -> Optional[HttpResponse]:
#         if is_patch(request) and request.content_type == "application/json":
#             validate_field = request.headers.get("X-DFV-Validate-Field")
#             value.is_valid()
#             fields = {}
#             for bound_field in value:
#                 widget = bound_field.field.widget
#                 fields[bound_field.name] = {
#                     "valid": len(bound_field.errors) == 0,
#                     "errors": str(value[bound_field.name].errors),
#                     "attrs": widget.attrs,
#                 }
#
#             return JsonResponse(
#                 {
#                     "name": validate_field,
#                     "fields": fields,
#                     "non_field_errors": str(value.non_field_errors()),
#                     "form_valid": value.is_valid(),
#                 }
#             )
#
#         return None


# def handle_form(
#     *, kwargs_factory: Optional[Callable[..., dict[str, Any]]] = None
# ) -> Any:
#     return InjectedParamForm(kwargs_factory=kwargs_factory)
