from typing import Any, Callable
from ...environment import get_global_environment
from .Scales import SCALES
from .GlobalConfig import global_config
from abc import ABC, abstractmethod
import itertools

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
        if isinstance(value, (tuple)):
            resolution = [self._resolve_pattern(v, 0) for v in value]
            return tuple(resolution)
            # return (self._convert(v) for v in value)
        elif isinstance(value, Pattern):
            return value
        else:
            raise ValueError(f"Unsupported value type for pattern operations: {type(value)}")

    def print_table(self, num_iterations=16, padding=1):
        """
        Prints a horizontal table of the SequencePattern with light ASCII boxes.
        Includes "Index" and "Value" labels at the beginning of each line.

        Args:
            num_iterations (int): The number of iterations to print. Default is 16.
            padding (int): Number of spaces to add on each side of the cell content. Default is 1.

        Returns:
            None
        """
        # Generate the data
        table_data = [(i, self(i)) for i in range(num_iterations)]

        # Find the maximum width for each cell
        cell_width = max(max(len(str(i)), len(str(v))) for i, v in table_data) + (
            padding * 2
        )  # Add padding to both sides

        # Set the label width
        label_width = max(len("Index"), len("Value")) + (padding * 2)

        # Create the box drawing characters
        top_border = (
            "┌"
            + "─" * label_width
            + "┬"
            + ("─" * cell_width + "┬") * (num_iterations - 1)
            + "─" * cell_width
            + "┐"
        )
        middle_border = (
            "├"
            + "─" * label_width
            + "┼"
            + ("─" * cell_width + "┼") * (num_iterations - 1)
            + "─" * cell_width
            + "┤"
        )
        bottom_border = (
            "└"
            + "─" * label_width
            + "┴"
            + ("─" * cell_width + "┴") * (num_iterations - 1)
            + "─" * cell_width
            + "┘"
        )

        # Create the format string for each cell
        label_format = f"│{{:^{label_width}}}"
        cell_format = f"│{{:^{cell_width}}}"

        # Print the table
        print(top_border)
        print(
            label_format.format("Index")
            + "".join(cell_format.format(str(i).center(cell_width - 2)) for i, _ in table_data)
        )
        print(middle_border)
        print(
            label_format.format("Value")
            + "".join(cell_format.format(str(v).center(cell_width - 2)) for _, v in table_data)
        )
        print(bottom_border)

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

    def __and__(self, other: "Pattern") -> "ConcatenatePattern":
        return ConcatenatePattern(self, other)

    def __rand__(self, other: "Pattern") -> "ConcatenatePattern":
        return ConcatenatePattern(other, self)

    def __or__(self, other: "Pattern") -> "SuperpositionPattern":
        return SuperpositionPattern(self, other)

    def __ror__(self, other: "Pattern") -> "SuperpositionPattern":
        return SuperpositionPattern(other, self)


class ArithmeticPattern(Pattern):
    """Base class for patterns that perform arithmetic operations on other patterns."""

    def __init__(self, pattern1: Pattern, pattern2: Pattern):
        super().__init__()
        self.pattern1 = pattern1
        self.pattern2 = pattern2

    @abstractmethod
    def operation(self, value1: Any, value2: Any) -> Any:
        pass

    # def __call__(self, iterator: int) -> Any:
    #     return self.operation(self.pattern1(iterator), self.pattern2(iterator))

    def __call__(self, iterator: int) -> Any:
        pattern1_result = self.pattern1(iterator) if callable(self.pattern1) else self.pattern1
        pattern2_result = self.pattern2(iterator) if callable(self.pattern2) else self.pattern2
        operation_result = (
            self.operation(pattern1_result, pattern2_result)
            if callable(self.operation)
            else self.operation
        )
        return operation_result

    def __len__(self) -> int:
        return len(self.pattern1)


class AddPattern(ArithmeticPattern):
    """Pattern that performs addition operation."""

    def operation(self, value1: Any, value2: Any) -> Any:
        if isinstance(value1, (list, tuple)) and isinstance(value2, (int, float)):
            return [v + value2 for v in value1]
        elif isinstance(value2, (list, tuple)) and isinstance(value1, (int, float)):
            return [value1 + v for v in value2]
        elif isinstance(value1, (list, tuple)) and isinstance(value2, (list, tuple)):
            if len(value1) > len(value2):
                value2 = list(itertools.islice(itertools.cycle(value2), len(value1)))
            else:
                value1 = list(itertools.islice(itertools.cycle(value1), len(value2)))
            return [v1 + v2 for v1, v2 in zip(value1, value2)]
        else:
            return value1 + value2

    # def operation(self, value1: Any, value2: Any) -> Any:
    #     if isinstance(value1, (list, tuple)) and isinstance(value2, (int, float)):
    #         return [v + value2 for v in value1]
    #     elif isinstance(value2, (list, tuple)) and isinstance(value1, (int, float)):
    #         return [value1 + v for v in value2]
    #     elif isinstance(value1, (list, tuple)) and isinstance(value2, (list, tuple)):
    #         return [v1 + v2 for v1, v2 in zip(value1, value2)]
    #     else:
    #         return value1 + value2


class SubtractPattern(ArithmeticPattern):
    """Pattern that performs subtraction operation."""

    def operation(self, value1: Any, value2: Any) -> Any:
        if isinstance(value1, (list, tuple)) and isinstance(value2, (int, float)):
            return [v - value2 for v in value1]
        elif isinstance(value2, (list, tuple)) and isinstance(value1, (int, float)):
            return [value1 - v for v in value2]
        elif isinstance(value1, (list, tuple)) and isinstance(value2, (list, tuple)):
            return [v1 - v2 for v1, v2 in zip(value1, value2)]
        else:
            return value1 - value2


class MultiplyPattern(ArithmeticPattern):
    """Pattern that performs multiplication operation."""

    def operation(self, value1: Any, value2: Any) -> Any:
        if isinstance(value1, (list, tuple)) and isinstance(value2, (int, float)):
            return [v * value2 for v in value1]
        elif isinstance(value2, (list, tuple)) and isinstance(value1, (int, float)):
            return [value1 * v for v in value2]
        elif isinstance(value1, (list, tuple)) and isinstance(value2, (list, tuple)):
            return [v1 * v2 for v1, v2 in zip(value1, value2)]
        else:
            return value1 * value2


class DividePattern(ArithmeticPattern):
    """Pattern that performs division operation."""

    def operation(self, value1: Any, value2: Any) -> Any:
        if isinstance(value1, (list, tuple)) and isinstance(value2, (int, float)):
            return [v / value2 for v in value1]
        elif isinstance(value2, (list, tuple)) and isinstance(value1, (int, float)):
            return [value1 / v for v in value2]
        elif isinstance(value1, (list, tuple)) and isinstance(value2, (list, tuple)):
            return [v1 / v2 for v1, v2 in zip(value1, value2)]
        else:
            return value1 / value2


class FloorDividePattern(ArithmeticPattern):
    """Pattern that performs floor division operation."""

    def operation(self, value1: Any, value2: Any) -> Any:
        if isinstance(value1, (list, tuple)) and isinstance(value2, (int, float)):
            return [v // value2 for v in value1]
        elif isinstance(value2, (list, tuple)) and isinstance(value1, (int, float)):
            return [value1 // v for v in value2]
        elif isinstance(value1, (list, tuple)) and isinstance(value2, (list, tuple)):
            return [v1 // v2 for v1, v2 in zip(value1, value2)]
        else:
            return value1 // value2


class ModuloPattern(ArithmeticPattern):
    """Pattern that performs modulo operation."""

    def operation(self, value1: Any, value2: Any) -> Any:
        if isinstance(value1, (list, tuple)) and isinstance(value2, (int, float)):
            return [v % value2 for v in value1]
        elif isinstance(value2, (list, tuple)) and isinstance(value1, (int, float)):
            return [value1 % v for v in value2]
        elif isinstance(value1, (list, tuple)) and isinstance(value2, (list, tuple)):
            return [v1 % v2 for v1, v2 in zip(value1, value2)]
        else:
            return value1 % value2


class PowerPattern(ArithmeticPattern):
    """Pattern that performs exponentiation operation."""

    def operation(self, value1: Any, value2: Any) -> Any:
        if isinstance(value1, (list, tuple)) and isinstance(value2, (int, float)):
            return [v**value2 for v in value1]
        elif isinstance(value2, (list, tuple)) and isinstance(value1, (int, float)):
            return [value1**v for v in value2]
        elif isinstance(value1, (list, tuple)) and isinstance(value2, (list, tuple)):
            return [v1**v2 for v1, v2 in zip(value1, value2)]
        else:
            return value1**value2


class LeftShiftPattern(ArithmeticPattern):
    """Pattern that performs left shift operation."""

    def operation(self, value1: Any, value2: Any) -> Any:
        if isinstance(value1, (list, tuple)) and isinstance(value2, (int, float)):
            return [v << value2 for v in value1]
        elif isinstance(value2, (list, tuple)) and isinstance(value1, (int, float)):
            return [value1 << v for v in value2]
        elif isinstance(value1, (list, tuple)) and isinstance(value2, (list, tuple)):
            return [v1 << v2 for v1, v2 in zip(value1, value2)]
        else:
            return value1 << value2


class RightShiftPattern(ArithmeticPattern):
    """Pattern that performs right shift operation."""

    def operation(self, value1: Any, value2: Any) -> Any:
        if isinstance(value1, (list, tuple)) and isinstance(value2, (int, float)):
            return [v >> value2 for v in value1]
        elif isinstance(value2, (list, tuple)) and isinstance(value1, (int, float)):
            return [value1 >> v for v in value2]
        elif isinstance(value1, (list, tuple)) and isinstance(value2, (list, tuple)):
            return [v1 >> v2 for v1, v2 in zip(value1, value2)]
        else:
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

    def __len__(self) -> int:
        return len(self.source_pattern)


class ConcatenatePattern(Pattern):
    def __init__(self, *patterns: Pattern):
        self.patterns = patterns
        self.lengths = [len(p) for p in patterns]
        self.total_length = sum(self.lengths)

    def __call__(self, iterator: int) -> Any:
        index = iterator % self.total_length
        for pattern, length in zip(self.patterns, self.lengths):
            if index < length:
                return pattern(index)
            index -= length

    def __len__(self) -> int:
        return self.total_length


class SuperpositionPattern(Pattern):
    def __init__(self, *patterns: Pattern):
        self.patterns = self._flatten_patterns(patterns)

    def _flatten_patterns(self, patterns):
        flattened = []
        for pattern in patterns:
            if isinstance(pattern, SuperpositionPattern):
                flattened.extend(pattern.patterns)
            else:
                flattened.append(pattern)
        return flattened

    def __call__(self, iterator: int) -> list:
        result = []
        for pattern in self.patterns:
            value = pattern(iterator % len(pattern))
            if isinstance(value, list):
                result.extend(value)
            else:
                result.append(value)
        return result

    def __len__(self) -> int:
        return max(len(p) for p in self.patterns)

    def __or__(self, other: "Pattern") -> "SuperpositionPattern":
        if isinstance(other, SuperpositionPattern):
            return SuperpositionPattern(*self.patterns, *other.patterns)
        else:
            return SuperpositionPattern(*self.patterns, other)
