from ..Pattern import Pattern
from ..Rest import Rest
from ....utils import euclidian_rhythm


class Peuclid(Pattern):
    """Generating euclidian rhythms.

    This class represents a generator for generating Euclidean rhythms.
    It takes the number of pulses, length, rotation, and base as parameters
    and generates a rhythm based on the Euclidean algorithm.

    Attributes:
        pulses (int or Pattern): The number of pulses in the rhythm.
        length (int or Pattern): The length of the rhythm.
        rotate (int or Pattern): The rotation of the rhythm.
        base (int or Pattern): The base value for the rhythm.

    Returns:
        int | Rest: The generated value based on the Euclidean rhythm.
    """

    def __init__(self, pulses, length, rotate=0, base=1):
        super().__init__()
        self.pulses = pulses
        self.length = length
        self.rotate = rotate
        self.base = base

    def __call__(self, iterator):
        pulses = self._resolve_pattern(self.pulses, iterator)
        length = self._resolve_pattern(self.length, iterator)
        rotate = self._resolve_pattern(self.rotate, iterator)
        base = self._resolve_pattern(self.base, iterator)

        self.rhythm = euclidian_rhythm(pulses, length, rotate)
        return base if self.rhythm[iterator % len(self.rhythm)] == 1 else Rest(base)


class Pbin(Pattern):
    """A pattern class that generates values based on a binary rhythm.

    Args:
        number (int | Pattern): The number used to generate the binary rhythm.
        base (int | Pattern, optional): The base value for the generated pattern. Defaults to 1.

    Returns:
        int | Rest: The generated value based on the binary rhythm.
    """

    def __init__(self, number: int | Pattern, base: int | Pattern = 1):
        super().__init__()
        self._number = number
        self._base = base

    def binary_rhythm(self, number: int) -> list:
        """Convert a number to its binary representation as a list of 1s and 0s.

        Args:
            number (int): The number to convert to binary.

        Returns:
            list: A list of 1s and 0s representing the binary number.
        """
        binary_string = format(number, "08b")
        return [int(bit) for bit in binary_string]

    def __call__(self, iterator):
        number = self._number(iterator) if isinstance(self._number, Pattern) else self._number
        base = self._base(iterator) if isinstance(self._base, Pattern) else self._base
        rhythm = self.binary_rhythm(number)
        index = iterator % len(rhythm)
        value = base if rhythm[index] == 1 else Rest(base)
        return value
