from ..Pattern import Pattern
from random import random


class Pinterp(Pattern):
    """
    A pattern that interpolates between two other patterns based on a given interpolation factor.

    Args:
        pattern_a (Pattern): The first pattern to interpolate between.
        pattern_b (Pattern): The second pattern to interpolate between.
        interpolation_factor (float or Pattern): The interpolation factor. If a float is provided, it represents a constant factor. If a Pattern is provided, it will be evaluated dynamically.

    Returns:
        The interpolated pattern based on the current interpolation factor.
    """

    def __init__(self, pattern_a, pattern_b, interpolation_factor):
        super().__init__()
        self.pattern_a = pattern_a
        self.pattern_b = pattern_b
        self.interpolation_factor = interpolation_factor

    def __call__(self, iterator):
        if isinstance(self.interpolation_factor, Pattern):
            current_factor = self.interpolation_factor(iterator)
        else:
            current_factor = self.interpolation_factor
        if random() < current_factor:
            return self.pattern_b(iterator)
        else:
            return self.pattern_a(iterator)


class Pcat(Pattern):
    """
    A pattern that applies multiple patterns in sequence.

    Args:
        *patterns: Variable number of patterns to be applied.

    Returns:
        A list of results obtained by applying each pattern in sequence.
    """

    def __init__(self, *patterns):
        super().__init__()
        self.patterns = patterns

    def __call__(self, iterator):
        result = []
        for pattern in self.patterns:
            if isinstance(pattern, Pattern):
                result.append(pattern(iterator))
            else:
                result.append(pattern)
        return result


class Ptpar(Pattern):
    """
    A pattern that applies multiple patterns with offsets to an iterator.

    Args:
        *patterns_with_offset: Variable number of tuples containing a pattern and an offset.

    Returns:
        A list of results obtained by applying each pattern with the given offset.
    """

    def __init__(self, *patterns_with_offset):
        super().__init__()
        self.patterns_with_offset = patterns_with_offset

    def __call__(self, iterator):
        return [
            self._get_value(pattern, iterator, offset)
            for pattern, offset in self.patterns_with_offset
        ]

    def _get_value(self, pattern, iterator, offset):
        if callable(pattern):
            return pattern(iterator + offset)
        else:
            return pattern


class Ppar(Pattern):
    """
    A pattern that applies multiple patterns in parallel.

    Args:
        *patterns: Variable number of patterns to be applied in parallel.

    Returns:
        A list of results obtained by applying each pattern in parallel.
    """

    def __init__(self, *patterns):
        super().__init__()
        self.patterns = patterns

    def __call__(self, iterator):
        return [pattern(iterator) if callable(pattern) else pattern for pattern in self.patterns]
