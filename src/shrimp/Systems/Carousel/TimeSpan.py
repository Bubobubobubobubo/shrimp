from functools import total_ordering
from typing import List, Self, Callable, Optional
from fractions import Fraction
import math

# Keeping these around because of the weird initial monkey patching
Fraction.sam = lambda self: TidalFraction(math.floor(self))
Fraction.next_sam = lambda self: TidalFraction(math.floor(self) + 1)
Fraction.whole_cycle = lambda self: (self.sam(), self.next_sam())
Fraction.cycle_pos = lambda self: self - self.sam()


class TidalFraction(Fraction):
    """Extended Fraction class with additional methods"""

    def sam(self) -> Self:
        """Returns the start of the cycle."""
        return TidalFraction(math.floor(self))

    def next_sam(self) -> Self:
        """Returns the start of the next cycle."""
        return self.sam() + 1

    def whole_cycle(self) -> Self:
        """Returns a TimeSpan representing the begin and end of the Time value's cycle"""

        return TimeSpan(self.sam(), self.next_sam())

    def cycle_pos(self) -> Self:
        """Returns the position of a time value relative to the start of its cycle."""
        return self - self.sam()

    @staticmethod
    def show_fraction(frac: Self) -> str:
        """Returns a string representation of a Fraction"""
        if frac is None:
            return str(frac)
        if frac.denominator == 1:
            return str(frac.numerator)

        result = {
            TidalFraction(1, 2): "½",
            TidalFraction(1, 3): "⅓",
            TidalFraction(2, 3): "⅔",
            TidalFraction(1, 4): "¼",
            TidalFraction(3, 4): "¾",
            TidalFraction(1, 5): "⅕",
            TidalFraction(2, 5): "⅖",
            TidalFraction(3, 5): "⅗",
            TidalFraction(4, 5): "⅘",
            TidalFraction(1, 6): "⅙",
            TidalFraction(5, 6): "⅚",
            TidalFraction(1, 7): "⅐",
            TidalFraction(1, 8): "⅛",
            TidalFraction(3, 8): "⅜",
            TidalFraction(5, 8): "⅝",
            TidalFraction(7, 8): "⅞",
            TidalFraction(1, 9): "⅑",
            TidalFraction(1, 10): "⅒",
        }.get(frac, None)

        if result:
            return result
        else:
            return f"({frac.numerator}/{frac.denominator})"

    def __repr__(self) -> str:
        return f"Frac({self.numerator}/{self.denominator})"

    def __str__(self) -> str:
        return TidalFraction.show_fraction(self)


@total_ordering
class TimeSpan:
    """TimeSpan represents a span from time X to time Y: (Time, Time)"""

    def __init__(self, begin: TidalFraction, end: TidalFraction):
        self.begin = TidalFraction(begin)
        self.end = TidalFraction(end)

    def span_cycles(self) -> List[Self]:
        """Splits a timespan at cycle boundaries"""
        spans = []
        begin = self.begin
        end = self.end
        end_sam = end.sam()

        while end > begin:
            # If begin and end are in the same cycle, we're done.
            if begin.sam() == end_sam:
                spans.append(TimeSpan(begin, self.end))
                break
            # add a timespan up to the next sam
            next_begin = begin.next_sam()
            spans.append(TimeSpan(begin, next_begin))

            # continue with the next cycle
            begin = next_begin
        return spans

    def with_time(self, func_time: Callable) -> Self:
        """Applies given function to both the begin and end time value of the timespan"""
        return TimeSpan(begin=func_time(self.begin), end=func_time(self.end))

    def intersection(self, other: Self, throw: bool = False) -> Optional[Self]:
        """Intersection of two timespans, returns None if they don't intersect."""
        intersect_begin = max(self.begin, other.begin)
        intersect_end = min(self.end, other.end)

        if intersect_begin > intersect_end:
            return None
        if intersect_begin == intersect_end:
            # Zero-width (point) intersection - doesn't intersect if it's at the end of a
            # non-zero-width timespan.

            if (intersect_begin == self.end and self.begin < self.end) or (
                intersect_begin == other.end and other.begin < other.end
            ):
                if throw:
                    raise ValueError(
                        f"TimeSpan {self} and TimeSpan {other} do not intersect"
                    )
                return

        return TimeSpan(intersect_begin, intersect_end)

    def midpoint(self) -> TidalFraction:
        """Returns the midpoint of the timespan"""
        return self.begin + ((self.end - self.begin) / 2)

    def __repr__(self) -> str:
        return f"Span({repr(self.begin)}, {repr(self.end)})"

    def __str__(self) -> str:
        return f"({TidalFraction.show_fraction(self.begin)}, {TidalFraction.show_fraction(self.end)})"

    def __eq__(self, other) -> bool:
        if isinstance(other, TimeSpan):
            return self.begin == other.begin and self.end == other.end
        return False

    def __le__(self, other) -> bool:
        return self.begin <= other.begin and self.end <= other.end
