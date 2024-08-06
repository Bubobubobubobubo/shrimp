from ..Pattern import Pattern
from typing import Optional


class Pexp(Pattern):
    """
    Represents an exponential pattern.

    Args:
        min (int | float | Pattern): The minimum value or pattern of values of the pattern.
        max (int | float | Pattern): The maximum value or pattern of values of the pattern.
        n (int | Pattern): The number of steps or pattern of steps in the pattern.
    """

    def __init__(self, min: int | float | Pattern, max: int | float | Pattern, n: int | Pattern):
        super().__init__()
        self.min = min
        self.max = max
        self.n = n

    def __call__(self, iterator):
        index = iterator % self.n
        min_value = self._resolve_pattern(self.min, iterator)
        max_value = self._resolve_pattern(self.max, iterator)
        n_value = self._resolve_pattern(self.n, iterator)
        return min_value * (max_value / min_value) ** (index / n_value)


class Plin(Pattern):
    """
    Represents a linear pattern that generates values between a start and end value.

    Args:
        start (int | float | Pattern): The starting value or pattern of values of the pattern.
        end (int | float | Pattern): The ending value or pattern of values of the pattern.
        n (int): The number of steps in the pattern.
    """

    def __init__(self, start: int | float | Pattern, end: int | float | Pattern, n: int):
        super().__init__()
        self.start = start
        self.end = end
        self.n = n

    def __call__(self, iterator):
        index = iterator % self.n

        start_value = (
            self._resolve_pattern(self.start, iterator)
            if isinstance(self.start, Pattern)
            else self.start
        )
        end_value = (
            self._resolve_pattern(self.end, iterator) if isinstance(self.end, Pattern) else self.end
        )
        return start_value + (end_value - start_value) * index / self.n


class Plog(Pattern):
    """
    Represents a Plog pattern that generates values based on a logarithmic progression.

    Args:
        start (int | float): The starting value of the pattern.
        end (int | float): The ending value of the pattern.
        n (int): The number of steps in the pattern.

    Returns:
        float: The value of the pattern at the given iterator position.
    """

    def __init__(self, start: int | float, end: int | float, n: int):
        super().__init__()
        self.start = start
        self.end = end
        self.n = n

    def __call__(self, iterator):
        index = iterator % self.n
        return self.start * (self.end / self.start) ** (index / self.n)


class Pgeom(Pattern):
    """
    A geometric pattern generator.

    This class represents a geometric pattern generator that produces a sequence of values
    based on a starting value, a common ratio, and a specified length.

    Raises:
        ValueError: If the length parameter 'len' is not specified for looping.

    Returns:
        float: The next value in the geometric sequence.
    """

    def __init__(self, start: float, ratio: float, len: Optional[int] = None):
        super().__init__()
        self.start = start
        self.ratio = ratio
        self.len = len

    def __call__(self, iterator):
        if self.len is None:
            raise ValueError("Length parameter 'len' must be specified for looping")

        index = iterator % self.len
        return self.start * (self.ratio**index)


class Parr(Pattern):
    """
    Represents a pattern that generates a sequence of values based on a start value, step size, and length.

    Args:
        start (float): The starting value of the pattern.
        step (float): The step size between each value in the pattern.
        len (Optional[int]): The length of the pattern. If not specified, the pattern will loop indefinitely.

    Returns:
        float: The next value in the pattern sequence.
    """

    def __init__(self, start: float, step: float, len: Optional[int] = None):
        super().__init__()
        self.start = start
        self.step = step
        self.len = len

    def __call__(self, iterator):
        if self.len is None:
            raise ValueError("Length parameter 'len' must be specified for looping")

        index = iterator % self.len
        return self.start + index * self.step
