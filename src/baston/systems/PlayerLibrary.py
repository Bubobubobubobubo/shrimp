import random
from ..utils import euclidian_rhythm
from .PScale import get_note_global
from typing import Optional
from functools import partial


Number: int | float

__ALL__ = ["prand"]


class Rest:
    def __init__(self, duration: int | float):
        self.duration = duration

    def __add__(self, other):
        return self.duration + other

    def __radd__(self, other):
        return other + self.duration

    def __sub__(self, other):
        return self.duration - other

    def __rsub__(self, other):
        return other - self.duration

    def __mul__(self, other):
        return self.duration * other

    def __rmul__(self, other):
        return other * self.duration

    def __truediv__(self, other):
        return self.duration / other

    def __rtruediv__(self, other):
        return other / self.duration

    def __mod__(self, other):
        return self.duration % other

    def __rmod__(self, other):
        return other % self.duration

    def __pow__(self, other):
        return self.duration**other

    def __rpow__(self, other):
        return other**self.duration

    def __lshift__(self, other):
        return self.duration << other

    def __rlshift__(self, other):
        return other << self.duration

    def __rshift__(self, other):
        return self.duration >> other

    def __rrshift__(self, other):
        return other >> self.duration


class Pattern:
    """Base class for all patterns. Patterns are used to generate sequences of values"""

    def __init__(self):
        pass

    def _convert(self, value):
        if isinstance(value, int):
            return PInt(value)
        elif isinstance(value, float):
            return PFloat(value)
        elif isinstance(value, Pattern):
            return value
        else:
            raise ValueError("Unsupported value type for pattern operations")

    def __call__(self, iterator):
        raise NotImplementedError("Subclasses should implement this!")

    def __add__(self, other):
        return AddPattern(self, self._convert(other))

    def __radd__(self, other):
        return AddPattern(self._convert(other), self)

    def __sub__(self, other):
        return SubPattern(self, self._convert(other))

    def __rsub__(self, other):
        return SubPattern(self._convert(other), self)

    def __mul__(self, other):
        return MulPattern(self, self._convert(other))

    def __rmul__(self, other):
        return MulPattern(self._convert(other), self)

    def __truediv__(self, other):
        return DivPattern(self, self._convert(other))

    def __rtruediv__(self, other):
        return DivPattern(self._convert(other), self)

    def __floordiv__(self, other):
        return FloorDivPattern(self, self._convert(other))

    def __rfloordiv__(self, other):
        return FloorDivPattern(self._convert(other), self)

    def __mod__(self, other):
        return ModuloPattern(self, self._convert(other))

    def __rmod__(self, other):
        return ModuloPattern(self._convert(other), self)

    def __pow__(self, other):
        return PowPattern(self, self._convert(other))

    def __rpow__(self, other):
        return PowPattern(self._convert(other), self)

    def __lshift__(self, other):
        return LShiftPattern(self, self._convert(other))

    def __rlshift__(self, other):
        return LShiftPattern(self._convert(other), self)

    def __rshift__(self, other):
        return RShiftPattern(self, self._convert(other))

    def __rrshift__(self, other):
        return RShiftPattern(self._convert(other), self)


class Pseq(Pattern):
    def __init__(self, *values):
        super().__init__()
        self.values = values

    def __call__(self, iterator):
        index = iterator % len(self.values)
        return self.values[index]


class PseqScale(Pseq):
    def __init__(self, *values, root: Optional[int] = None):
        super().__init__()
        self.values = values
        self._root = root

    def __call__(self, iterator):
        index = iterator % len(self.values)
        value = self.values[index]
        # TODO: this is broken
        return (
            get_note_global(value)
            if isinstance(value, int)
            else list(map(lambda x: get_note_global(x), value))
        )


class AddPattern(Pattern):
    def __init__(self, p1, p2):
        super().__init__()
        self.p1 = p1
        self.p2 = p2

    def __call__(self, iterator):
        return self.p1(iterator) + self.p2(iterator)


class SubPattern(Pattern):
    def __init__(self, p1, p2):
        super().__init__()
        self.p1 = p1
        self.p2 = p2

    def __call__(self, iterator):
        return self.p1(iterator) - self.p2(iterator)


class MulPattern(Pattern):
    def __init__(self, p1, p2):
        super().__init__()
        self.p1 = p1
        self.p2 = p2

    def __call__(self, iterator):
        return self.p1(iterator) * self.p2(iterator)


class FloorDivPattern(Pattern):
    def __init__(self, p1, p2):
        super().__init__()
        self.p1 = p1
        self.p2 = p2

    def __call__(self, iterator):
        return self.p1(iterator) // self.p2(iterator)


class DivPattern(Pattern):
    def __init__(self, p1, p2):
        super().__init__()
        self.p1 = p1
        self.p2 = p2

    def __call__(self, iterator):
        return self.p1(iterator) / self.p2(iterator)


class ModuloPattern(Pattern):
    def __init__(self, p1, p2):
        super().__init__()
        self.p1 = p1
        self.p2 = p2

    def __call__(self, iterator):
        return self.p1(iterator) % self.p2(iterator)


class PowPattern(Pattern):
    def __init__(self, p1, p2):
        super().__init__()
        self.p1 = p1
        self.p2 = p2

    def __call__(self, iterator):
        return self.p1(iterator) ** self.p2(iterator)


class LShiftPattern(Pattern):
    def __init__(self, p1, p2):
        super().__init__()
        self.p1 = p1
        self.p2 = p2

    def __call__(self, iterator):
        return self.p1(iterator) << self.p2(iterator)


class RShiftPattern(Pattern):
    def __init__(self, p1, p2):
        super().__init__()
        self.p1 = p1
        self.p2 = p2

    def __call__(self, iterator):
        return self.p1(iterator) << self.p2(iterator)


class Prand(Pattern):
    def __init__(self, min: int | float, max: int | float, return_integer: bool = True):
        super().__init__()
        self.min = min
        self.max = max
        self.return_integer = return_integer

    def __call__(self, _):
        if self.return_integer:
            return random.randint(self.min, self.max)
        else:
            return random.uniform(self.min, self.max)


class Pchoose(Pattern):
    def __init__(self, *values):
        super().__init__()
        self.values = values

    def __call__(self, _):
        return random.choice(self.values)


class PInt(Pattern):
    def __init__(self, value: int):
        super().__init__()
        self.value = value

    def __call__(self, _):
        return self.value


class PFloat(Pattern):
    def __init__(self, value: float):
        super().__init__()
        self.value = value

    def __call__(self, _):
        return self.value


class Place(Pattern):
    def __init__(self, p1, p2):
        super().__init__()
        self.p1 = p1
        self.p2 = p2

    def __call__(self, iterator):
        if iterator % 2 == 0:
            return self.p1(iterator // 2)
        else:
            return self.p2(iterator // 2)


class Peuclid(Pattern):
    """Generating euclidian rhythms.

    TODO: convert so Rests are usable.
    """

    def __init__(self, pulses: int, length: int, rotate: int = 0):
        super().__init__()
        self.rhythm = euclidian_rhythm(pulses, length, rotate)

    def __call__(self, iterator):
        index = iterator % len(self.rhythm)
        return self.rhythm[index]
