import random
from typing import Optional
from typing import Any
from ...environment import get_global_environment
from .Scales import SCALES
from .GlobalConfig import global_config
from abc import ABC, abstractmethod

Number: int | float


class Pattern(ABC):
    """Base class for all patterns. Patterns are used to generate sequences of values."""

    env = get_global_environment()
    _config = global_config

    def __init__(self):
        pass

    @property
    def variables(self):
        return self._config._register

    @variables.setter
    def variables(self, value):
        self._config._register = value

    @property
    def root(self) -> int:
        return self._config.root

    @root.setter
    def root(self, value: int):
        self._config.root = value

    @property
    def scale(self) -> list[int]:
        return self._config.scale

    @scale.setter
    def scale(self, value: list[int]):
        self._config.scale = value

    @abstractmethod
    def __call__(self, iterator: int) -> Any:
        """Generate the next value in the pattern sequence."""
        pass

    def _resolve_pattern(self, pattern: Any, iterator: int) -> Any:
        if isinstance(pattern, Pattern):
            return pattern(iterator)
        return pattern

    def _convert(self, value: Any) -> "Pattern":
        if isinstance(value, (int, float)):
            return ConstantPattern(value)
        elif isinstance(value, Pattern):
            return value
        else:
            raise ValueError(f"Unsupported value type for pattern operations: {type(value)}")

    def int(self) -> "IntegerPattern":
        """
        Returns a new pattern that always outputs integers.
        """
        return IntegerPattern(self)

    def __add__(self, other: Any) -> "ArithmeticPattern":
        return AddPattern(self, self._convert(other))

    def __radd__(self, other: Any) -> "ArithmeticPattern":
        return AddPattern(self._convert(other), self)

    def __sub__(self, other: Any) -> "ArithmeticPattern":
        return SubtractPattern(self, self._convert(other))

    def __rsub__(self, other: Any) -> "ArithmeticPattern":
        return SubtractPattern(self._convert(other), self)

    def __mul__(self, other: Any) -> "ArithmeticPattern":
        return MultiplyPattern(self, self._convert(other))

    def __rmul__(self, other: Any) -> "ArithmeticPattern":
        return MultiplyPattern(self._convert(other), self)

    def __truediv__(self, other: Any) -> "ArithmeticPattern":
        return DividePattern(self, self._convert(other))

    def __rtruediv__(self, other: Any) -> "ArithmeticPattern":
        return DividePattern(self._convert(other), self)

    def __floordiv__(self, other: Any) -> "ArithmeticPattern":
        return FloorDividePattern(self, self._convert(other))

    def __rfloordiv__(self, other: Any) -> "ArithmeticPattern":
        return FloorDividePattern(self._convert(other), self)

    def __mod__(self, other: Any) -> "ArithmeticPattern":
        return ModuloPattern(self, self._convert(other))

    def __rmod__(self, other: Any) -> "ArithmeticPattern":
        return ModuloPattern(self._convert(other), self)

    def __pow__(self, other: Any) -> "ArithmeticPattern":
        return PowerPattern(self, self._convert(other))

    def __rpow__(self, other: Any) -> "ArithmeticPattern":
        return PowerPattern(self._convert(other), self)

    def __lshift__(self, other: Any) -> "ArithmeticPattern":
        return LeftShiftPattern(self, self._convert(other))

    def __rlshift__(self, other: Any) -> "ArithmeticPattern":
        return LeftShiftPattern(self._convert(other), self)

    def __rshift__(self, other: Any) -> "ArithmeticPattern":
        return RightShiftPattern(self, self._convert(other))

    def __rrshift__(self, other: Any) -> "ArithmeticPattern":
        return RightShiftPattern(self._convert(other), self)


class ArithmeticPattern(Pattern):
    """Base class for patterns that perform arithmetic operations on other patterns."""

    def __init__(self, pattern1: Pattern, pattern2: Pattern):
        super().__init__()
        self.pattern1 = pattern1
        self.pattern2 = pattern2

    @abstractmethod
    def operation(self, value1: Any, value2: Any) -> Any:
        pass

    def __call__(self, iterator: int) -> Any:
        return self.operation(self.pattern1(iterator), self.pattern2(iterator))


class AddPattern(ArithmeticPattern):
    """Pattern that performs addition operation."""

    def operation(self, value1: Any, value2: Any) -> Any:
        return value1 + value2


class SubtractPattern(ArithmeticPattern):
    """Pattern that performs subtraction operation."""

    def operation(self, value1: Any, value2: Any) -> Any:
        return value1 - value2


class MultiplyPattern(ArithmeticPattern):
    """Pattern that performs multiplication operation."""

    def operation(self, value1: Any, value2: Any) -> Any:
        return value1 * value2


class DividePattern(ArithmeticPattern):
    """Pattern that performs division operation."""

    def operation(self, value1: Any, value2: Any) -> Any:
        return value1 / value2


class FloorDividePattern(ArithmeticPattern):
    """Pattern that performs floor division operation."""

    def operation(self, value1: Any, value2: Any) -> Any:
        return value1 // value2


class ModuloPattern(ArithmeticPattern):
    """Pattern that performs modulo operation."""

    def operation(self, value1: Any, value2: Any) -> Any:
        return value1 % value2


class PowerPattern(ArithmeticPattern):
    """Pattern that performs exponentiation operation."""

    def operation(self, value1: Any, value2: Any) -> Any:
        return value1**value2


class LeftShiftPattern(ArithmeticPattern):
    """Pattern that performs left shift operation."""

    def operation(self, value1: Any, value2: Any) -> Any:
        return value1 << value2


class RightShiftPattern(ArithmeticPattern):
    """Pattern that performs right shift operation."""

    def operation(self, value1: Any, value2: Any) -> Any:
        return value1 >> value2


class ConstantPattern(Pattern):
    """A pattern that always returns the same value."""

    def __init__(self, value: Any):
        super().__init__()
        self.value = value

    def __call__(self, iterator: int) -> Any:
        return self.value


class IntegerPattern(Pattern):
    """A pattern that wraps another pattern and always returns integer values."""

    def __init__(self, source_pattern: Pattern):
        super().__init__()
        self.source_pattern = source_pattern

    def __call__(self, iterator: int) -> int:
        result = self.source_pattern(iterator)
        return int(round(result))
