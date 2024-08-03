from functools import total_ordering
from pprint import pformat
from typing import Any, Callable, Self
from .TimeSpan import TimeSpan


@total_ordering
class Event:
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

    def whole_or_part(self) -> TimeSpan:
        """Returns the 'whole' timespan if it's present, otherwise the 'part'."""
        return self.whole if self.whole else self.part

    def with_span(self, func: Callable) -> Self:
        """Returns a new event with the function f applies to the event timespan."""
        whole = None if not self.whole else func(self.whole)
        return Event(whole, func(self.part), self.value)

    def with_value(self, func: Callable) -> Self:
        """Returns a new event with the function f applies to the event value."""
        return Event(self.whole, self.part, func(self.value))

    def has_onset(self) -> bool:
        """Test whether the event contains the onset, i.e that
        the beginning of the part is the same as that of the whole timespan."""
        return self.whole and self.whole.begin == self.part.begin

    def __repr__(self) -> str:
        return f"Event({repr(self.whole)}, {repr(self.part)}, {repr(self.value)})"

    def __str__(self) -> str:
        return f"({self.whole}, {self.part}, {pformat(self.value)})"

    def __eq__(self, other) -> bool:
        if isinstance(other, Event):
            return (
                self.whole == other.whole
                and self.part == other.part
                and self.value == other.value
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
