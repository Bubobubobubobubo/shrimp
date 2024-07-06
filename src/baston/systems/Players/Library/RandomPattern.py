from ..Pattern import Pattern
from typing import Optional
import random


class Pcoin(Pattern):
    """
    A pattern that returns True with a probability `p`.

    Args:
        p (float): The probability of returning True.

    Returns:
        bool: True with probability `p`, False otherwise.
    """

    def __init__(self, p: float):
        super().__init__()
        self.p = p

    def __call__(self, _):
        return random.random() < self.p


class Prand(Pattern):
    """
    A pattern that generates random numbers within a given range.

    Args:
        min (int | float | Pattern): The minimum value of the range.
        max (int | float | Pattern): The maximum value of the range.
        as_float (bool, optional): If True, the generated numbers will be returned as floats.
            If False (default), the generated numbers will be returned as integers.

    Returns:
        int | float: A random number within the specified range.
    """

    def __init__(
        self, min: int | float | Pattern, max: int | float | Pattern, as_float: bool = False
    ):
        super().__init__()
        self.min = min
        self.max = max
        self.return_integer = as_float

    def __call__(self, _):
        min_value = self._resolve_pattern(self.min, _)
        max_value = self._resolve_pattern(self.max, _)
        if self.return_integer:
            return random.randint(int(min_value), int(max_value))
        else:
            return random.uniform(min_value, max_value)


class Pchoose(Pattern):
    """
    A pattern that randomly chooses a value from a given set of values.

    Args:
        *values: Variable number of values to choose from.

    Returns:
        The randomly chosen value.
    """

    def __init__(self, *values):
        super().__init__()
        self.values = values

    def __call__(self, _):
        return random.choice(self.values)


class Pwchoose(Pattern):
    """
    A pattern that chooses a value from a set of values with optional weights.

    Args:
        *values: Variable number of values to choose from.
        weights (Optional[list[float]]): Optional list of weights corresponding to the values.
        If not provided, all values are equally weighted.

    Returns:
        The chosen value.
    """

    def __init__(self, *values, weights: Optional[list[float]] = None):
        super().__init__()
        self.values = values
        if weights is None:
            self.weights = [1] * len(values)
        else:
            self.weights = weights

    def __call__(self, iterator):
        resolved_weights = [w(iterator) if isinstance(w, Pattern) else w for w in self.weights]
        return random.choices(self.values, weights=resolved_weights)[0]
