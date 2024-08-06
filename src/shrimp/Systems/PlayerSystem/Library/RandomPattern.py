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
        self._as_float = as_float

    def __call__(self, _):
        min_value = self._resolve_pattern(self.min, _)
        max_value = self._resolve_pattern(self.max, _)
        if self._as_float:
            return random.uniform(min_value, max_value)
        else:
            return random.randint(int(min_value), int(max_value))


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
    A pattern that randomly chooses a value from a given set of values based on weighted probabilities.

    Args:
        *values: Variable number of values to choose from.
        weights: List of weights corresponding to the values.

    Returns:
        The randomly chosen value based on weights.
    """

    def __init__(self, *values, weights):
        super().__init__()
        if len(values) != len(weights):
            raise ValueError("The number of values must match the number of weights.")
        self.values = values
        self.weights = weights

    def __call__(self, _):
        return random.choices(self.values, weights=self.weights, k=1)[0]


class Phuman(Pattern):
    """
    A humanization pattern that takes a value and slightly deviates from it.

    Args:
        value (int | float | Pattern): The input value to humanize.
        deviation (float): The maximum percentage deviation (0-1) from the original value.

    Returns:
        int | float: The humanized value.
    """

    def __init__(self, value: int | float | Pattern, deviation: float = 0.05):
        super().__init__()
        self.value = value
        self.deviation = deviation

    def __call__(self, _):
        original_value = self._resolve_pattern(self.value, _)
        deviation_amount = original_value * self.deviation
        humanized_value = random.uniform(
            original_value - deviation_amount, original_value + deviation_amount
        )
        return humanized_value
