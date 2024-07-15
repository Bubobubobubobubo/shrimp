class Rest:
    """
    Represents a rest in a musical pattern.

    Args:
        duration (int | float): The duration of the rest.
    """

    def __init__(self, duration: int | float):
        self.duration = duration

    def __add__(self, other):
        return Rest(self.duration + other)

    def __radd__(self, other):
        return Rest(other + self.duration)

    def __sub__(self, other):
        return Rest(self.duration - other)

    def __rsub__(self, other):
        return Rest(other - self.duration)

    def __mul__(self, other):
        return Rest(self.duration * other)

    def __rmul__(self, other):
        return Rest(other * self.duration)

    def __truediv__(self, other):
        return Rest(self.duration / other)

    def __rtruediv__(self, other):
        return Rest(other / self.duration)

    def __mod__(self, other):
        return Rest(self.duration % other)

    def __rmod__(self, other):
        return Rest(other % self.duration)

    def __pow__(self, other):
        return Rest(self.duration**other)

    def __rpow__(self, other):
        return Rest(other**self.duration)

    def __lshift__(self, other):
        return Rest(self.duration << other)

    def __rlshift__(self, other):
        return Rest(other << self.duration)

    def __rshift__(self, other):
        return Rest(self.duration >> other)

    def __rrshift__(self, other):
        return Rest(other >> self.duration)

    def __lt__(self, other):
        if isinstance(other, Rest):
            return self.duration < other.duration
        return self.duration < other

    def __le__(self, other):
        if isinstance(other, Rest):
            return self.duration <= other.duration
        return self.duration <= other

    def __gt__(self, other):
        if isinstance(other, Rest):
            return self.duration > other.duration
        return self.duration > other

    def __ge__(self, other):
        if isinstance(other, Rest):
            return self.duration >= other.duration
        return self.duration >= other

    def __repr__(self) -> str:
        return f"Rest({self.duration})"

    def __str__(self) -> str:
        return f"Rest({self.duration})"

    def to_number(self):
        """
        Converts the duration of the rest to a number.

        Returns:
            int | float: The duration of the rest as a number.

        """
        return self.duration
