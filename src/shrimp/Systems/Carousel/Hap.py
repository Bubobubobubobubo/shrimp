from functools import total_ordering
from pprint import pformat
from typing import Any, Callable, Self
from .TimeSpan import TimeSpan


@total_ordering
class Hap:
    """
    Event class, representing a value active during the timespan
    'part'. This might be a fragment of an event, in which case the
    timespan will be smaller than the 'whole' timespan, otherwise the
    two timespans will be the same. The 'part' must never extend outside of the
    'whole'. If the event represents a continuously changing value
    then the whole will be returned as None, in which case the given
    value will have been sampled from the point halfway between the
    start and end of the 'part' timespan.
    """

    def __init__(self, whole: TimeSpan, part: TimeSpan, value: Any):
        self.whole = whole
        self.part = part
        self.value = value

    def end_clipped(self) -> Self:
        """TODO: ???"""
        return self.whole.begin.add(self.duration)

    def is_active(self, current_time: int | float) -> bool:
        """Test whether the event is active at the given time."""
        return self.whole.begin <= current_time and self.end_clipped() >= current_time

    def is_in_past(self, current_time: int | float) -> bool:
        """Test whether the event is in the past at the given time."""
        return self.end_clipped() < current_time

    def is_in_future(self, current_time: int | float) -> bool:
        """Test whether the event is in the future at the given time."""
        return self.whole.begin > current_time

    def is_in_near_future(self, margin: int | float, current_time: int | float) -> bool:
        """Test whether the event is in the near future at the given time."""
        return current_time < self.whole.begin and current_time > self.whole.begin - margin

    def is_within_time(self, min_time: int | float, max_time: int | float) -> bool:
        """Test whether the event is within the given time range."""
        return self.whole.begin >= min_time and self.end_clipped() <= max_time

    def whole_or_part(self) -> TimeSpan:
        """Returns the 'whole' timespan if it's present, otherwise the 'part'."""
        return self.whole if self.whole else self.part

    def with_span(self, func: Callable) -> Self:
        """Returns a new event with the function f applies to the event timespan."""
        whole = None if not self.whole else func(self.whole)
        return Hap(whole, func(self.part), self.value)

    def with_value(self, func: Callable) -> Self:
        """Returns a new event with the function f applies to the event value."""
        return Hap(self.whole, self.part, func(self.value))

    def has_onset(self) -> bool:
        """Test whether the event contains the onset, i.e that
        the beginning of the part is the same as that of the whole timespan."""
        return self.whole and self.whole.begin == self.part.begin

    # has_tag

    def span_equals(self, other) -> bool:
        """Test whether the event timespan is the same as the given event timespan."""
        return (not self.whole and not other.whole) or self.whole == other.whole

    def __repr__(self) -> str:
        return f"Event({repr(self.whole)}, {repr(self.part)}, {repr(self.value)})"

    def __str__(self) -> str:
        return f"({self.whole}, {self.part}, {pformat(self.value)})"

    def __eq__(self, other) -> bool:
        if isinstance(other, Hap):
            return (
                self.whole == other.whole and self.part == other.part and self.value == other.value
            )
        return False

    def __le__(self, other) -> bool:
        return (
            self.whole
            and other.whole
            and self.whole <= other.whole
            and self.part
            and other.part
            and self.part <= other.part
        )
