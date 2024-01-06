from typing import Any, Callable, cast, Optional, TypeAlias

from django.http import HttpRequest, HttpResponseBase

from dfv import is_get, is_post

ACTION_FN: TypeAlias = Callable[[str], Optional[HttpResponseBase]]


class Actions:
    actions: dict[str, ACTION_FN]
    request: HttpRequest
    param_dict: dict
    __return_value: Any = None

    def __init__(self, request: HttpRequest):
        self.actions = {}
        self.request = request

        if is_get(request, ignore_view_stack=False):
            self.param_dict = cast(dict, request.GET)
        elif is_post(request):
            self.param_dict = cast(dict, request.POST)
        else:
            self.param_dict = {}

    def add(self, action_fn: ACTION_FN):
        """
        Adds an action to the list of actions to check.
        """
        fn_name = action_fn.__name__
        self.actions[fn_name] = action_fn
        return action_fn

    def matched(self) -> bool:
        """
        Returns True if an action was matched, False otherwise.
        """
        self.__return_value = self.check(self.param_dict)
        return self.__return_value is not None

    @property
    def value(self) -> Any:
        """
        Returns the return value of the matched action.
        """
        return self.__return_value

    def check(self, param_dict):
        """
        Checks if any of the actions matches and returns the return value of the matched action.
        """
        for action_name, action_fn in self.actions.items():
            if action_name in param_dict:
                return action_fn(param_dict[action_name])

        return None
