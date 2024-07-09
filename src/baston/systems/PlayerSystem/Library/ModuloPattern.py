from ..Pattern import Pattern


class Pmbeat(Pattern):
    """
    Pmbeat class represents a pattern that alternates between two values based on the current beat of the clock.

    Args:
        period (int | float): The period of the pattern in beats.
        *values: Variable number of values to alternate between.

    Returns:
        The resolved pattern value based on the current beat of the clock.
    """

    def __init__(self, period: int | float, *values):
        super().__init__()
        self.period = period
        self._values = values

    def __call__(self, _):
        if self.env.clock.beat % self.period <= (self.period / 2):
            return self._resolve_pattern(self._values[0], _)
        else:
            return self._resolve_pattern(self._values[1], _)


class Pmbar(Pattern):
    """
    Pmbar class represents a pattern that alternates between two values based on the current bar of the clock.

    Args:
        period (int | float): The period of the pattern in beats.
        *values: Variable number of values to alternate between.

    Returns:
        The resolved pattern value based on the current beat of the clock.
    """

    def __init__(self, period: int | float, *values):
        super().__init__()
        self.period = period
        self._values = values

    def __call__(self, _):
        if self.env.clock.bar % self.period <= (self.period / 2):
            return self._resolve_pattern(self._values[0], _)
        else:
            return self._resolve_pattern(self._values[1], _)
