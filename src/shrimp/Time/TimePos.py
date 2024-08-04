from dataclasses import dataclass


@dataclass
class TimePos:
    """A class to represent a time position in a musical context."""

    bar: int = 1
    beat: int = 0
    phase: float = 0

    def __eq__(self, other):
        if not isinstance(other, TimePos):
            return NotImplemented
        return (self.bar, self.beat, self.phase) == (other.bar, other.beat, other.phase)

    def __lt__(self, other):
        if not isinstance(other, TimePos):
            return NotImplemented
        return (self.bar, self.beat, self.phase) < (other.bar, other.beat, other.phase)

    def __le__(self, other):
        if not isinstance(other, TimePos):
            return NotImplemented
        return (self.bar, self.beat, self.phase) <= (other.bar, other.beat, other.phase)

    def __gt__(self, other):
        if not isinstance(other, TimePos):
            return NotImplemented
        return (self.bar, self.beat, self.phase) > (other.bar, other.beat, other.phase)

    def __ge__(self, other):
        if not isinstance(other, TimePos):
            return NotImplemented
        return (self.bar, self.beat, self.phase) >= (other.bar, other.beat, other.phase)

    def __eq__(self, other):
        if not isinstance(other, TimePos):
            return NotImplemented
        return (self.bar, self.beat, self.phase) == (other.bar, other.beat, other.phase)

    def __lt__(self, other):
        if not isinstance(other, TimePos):
            return NotImplemented
        return (self.bar, self.beat, self.phase) < (other.bar, other.beat, other.phase)

    def __le__(self, other):
        if not isinstance(other, TimePos):
            return NotImplemented
        return (self.bar, self.beat, self.phase) <= (other.bar, other.beat, other.phase)

    def __gt__(self, other):
        if not isinstance(other, TimePos):
            return NotImplemented
        return (self.bar, self.beat, self.phase) > (other.bar, other.beat, other.phase)

    def __ge__(self, other):
        if not isinstance(other, TimePos):
            return NotImplemented
        return (self.bar, self.beat, self.phase) >= (other.bar, other.beat, other.phase)
