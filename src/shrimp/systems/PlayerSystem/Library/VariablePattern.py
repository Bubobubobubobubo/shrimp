from ..Pattern import Pattern
from typing import Any, Optional
from ..GlobalConfig import global_config


class Pget(Pattern):
    """
    A pattern that retrieves a variable from the pattern's variable namespace.
    Args:
        var_name (str): The name of the variable to retrieve.
        default (Optional[Any]): The default value to return if the variable is not found.
    Returns:
        Any: The value of the variable, or the default value if not found.
    """

    def __init__(self, var_name: str, default: Optional[Any] = None):
        super().__init__()
        self._var_name = var_name
        self._default_value = default

    def __call__(self, iterator: int) -> Any:
        if self._var_name in self.variables:
            value = self.variables.get(self._var_name, self._default_value)
            return self._resolve_pattern(value, iterator)
        else:
            return self._default_value


class Pset(Pattern):
    """
    A pattern that sets a variable in the pattern's variable namespace and returns its value.
    Args:
        var_name (str): The name of the variable to set.
        value (Any): The value or pattern to assign to the variable.
    Returns:
        Any: The value that was set, or the result of calling the pattern if it's a Pattern.
    """

    def __init__(self, var_name: str, value: Any):
        super().__init__()
        self._var_name = var_name
        self._value = value

    def __call__(self, iterator: int) -> Any:
        self.variables[self._var_name] = self._value
        if isinstance(self._value, Pattern):
            return self._value(iterator)
        return self._value
