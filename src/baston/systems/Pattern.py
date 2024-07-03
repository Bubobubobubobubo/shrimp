import random
import math
from ..utils import euclidian_rhythm
from typing import Optional, Callable
from typing import Any
from ..environment import get_global_environment
from .Scales import SCALES
from .Rest import Rest

Number: int | float


class GlobalConfig:
    """
    Singleton class representing the global configuration.

    This class ensures that only one instance of the GlobalConfig class is created
    and provides access to global properties.

    Attributes:
        _instance (GlobalConfig): The singleton instance of the GlobalConfig class.
        scale (str): The current scale.
        root (int): The root note.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalConfig, cls).__new__(cls)
            cls._instance.scale = "major"
            cls._register = {}
            cls._root_note = 60
        return cls._instance

    @property
    def register(self):
        return self._instance._register

    @register.setter
    def register(self, value):
        self._instance._register = value

    @property
    def scale(self):
        return self._instance._scale

    @scale.setter
    def scale(self, value):
        self._instance._scale = value

    @property
    def root(self):
        return self._instance._root_note

    @root.setter
    def root(self, value):
        self._instance._root_note = value


global_config = GlobalConfig()


class Pattern:
    """Base class for all patterns. Patterns are used to generate sequences of values"""

    def __init__(self):
        self.env = get_global_environment()

    @property
    def root(self):
        return global_config.root

    @root.setter
    def root(self, value):
        global_config.root = value

    @property
    def scale(self):
        return global_config.scale

    @scale.setter
    def scale(self, value):
        global_config.scale = value

    def _convert(self, value):
        if isinstance(value, int):
            return _Pint(value)
        elif isinstance(value, float):
            return _PFloat(value)
        elif isinstance(value, Pattern):
            return value
        else:
            raise ValueError("Unsupported value type for pattern operations")

    def __call__(self, iterator):
        raise NotImplementedError("Subclasses should implement this!")

    def __add__(self, other):
        return _AddPattern(self, self._convert(other))

    def __radd__(self, other):
        return _AddPattern(self._convert(other), self)

    def __sub__(self, other):
        return _SubPattern(self, self._convert(other))

    def __rsub__(self, other):
        return _SubPattern(self._convert(other), self)

    def __mul__(self, other):
        return _MulPattern(self, self._convert(other))

    def __rmul__(self, other):
        return _MulPattern(self._convert(other), self)

    def __truediv__(self, other):
        return _DivPattern(self, self._convert(other))

    def __rtruediv__(self, other):
        return _DivPattern(self._convert(other), self)

    def __floordiv__(self, other):
        return _FloorDivPattern(self, self._convert(other))

    def __rfloordiv__(self, other):
        return _FloorDivPattern(self._convert(other), self)

    def __mod__(self, other):
        return _ModuloPattern(self, self._convert(other))

    def __rmod__(self, other):
        return _ModuloPattern(self._convert(other), self)

    def __pow__(self, other):
        return _PowPattern(self, self._convert(other))

    def __rpow__(self, other):
        return _PowPattern(self._convert(other), self)

    def __lshift__(self, other):
        return _LShiftPattern(self, self._convert(other))

    def __rlshift__(self, other):
        return _LShiftPattern(self._convert(other), self)

    def __rshift__(self, other):
        return _RShiftPattern(self, self._convert(other))

    def __rrshift__(self, other):
        return _RShiftPattern(self._convert(other), self)


class _AddPattern(Pattern):
    def __init__(self, p1, p2):
        super().__init__()
        self.p1 = p1
        self.p2 = p2

    def __call__(self, iterator):
        return self.p1(iterator) + self.p2(iterator)


class _SubPattern(Pattern):
    def __init__(self, p1, p2):
        super().__init__()
        self.p1 = p1
        self.p2 = p2

    def __call__(self, iterator):
        return self.p1(iterator) - self.p2(iterator)


class _MulPattern(Pattern):
    def __init__(self, p1, p2):
        super().__init__()
        self.p1 = p1
        self.p2 = p2

    def __call__(self, iterator):
        return self.p1(iterator) * self.p2(iterator)


class _FloorDivPattern(Pattern):
    def __init__(self, p1, p2):
        super().__init__()
        self.p1 = p1
        self.p2 = p2

    def __call__(self, iterator):
        return self.p1(iterator) // self.p2(iterator)


class _DivPattern(Pattern):
    def __init__(self, p1, p2):
        super().__init__()
        self.p1 = p1
        self.p2 = p2

    def __call__(self, iterator):
        return self.p1(iterator) / self.p2(iterator)


class _ModuloPattern(Pattern):
    def __init__(self, p1, p2):
        super().__init__()
        self.p1 = p1
        self.p2 = p2

    def __call__(self, iterator):
        return self.p1(iterator) % self.p2(iterator)


class _PowPattern(Pattern):
    def __init__(self, p1, p2):
        super().__init__()
        self.p1 = p1
        self.p2 = p2

    def __call__(self, iterator):
        return self.p1(iterator) ** self.p2(iterator)


class _LShiftPattern(Pattern):
    def __init__(self, p1, p2):
        super().__init__()
        self.p1 = p1
        self.p2 = p2

    def __call__(self, iterator):
        return self.p1(iterator) << self.p2(iterator)


class _RShiftPattern(Pattern):
    def __init__(self, p1, p2):
        super().__init__()
        self.p1 = p1
        self.p2 = p2

    def __call__(self, iterator):
        return self.p1(iterator) << self.p2(iterator)


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
        self.return_integer = as_float

    def __call__(self, _):
        min_value = self._resolve_pattern(self.min, _)
        max_value = self._resolve_pattern(self.max, _)
        if self.return_integer:
            return random.randint(int(min_value), int(max_value))
        else:
            return random.uniform(min_value, max_value)

    def _resolve_pattern(self, pattern, iterator):
        if isinstance(pattern, Pattern):
            return pattern(iterator)
        else:
            return pattern


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


class _Pint(Pattern):
    def __init__(self, value: int):
        super().__init__()
        self.value = value

    def __call__(self, _):
        return self.value


class Pint(Pattern):
    def __init__(self, value: Any):
        super().__init__()
        self.value = value

    def __call__(self, iterator):
        value = self.value(iterator)
        try:
            return int(value)
        except ValueError:
            return value


class _PFloat(Pattern):
    def __init__(self, value: float):
        super().__init__()
        self.value = value

    def __call__(self, _):
        return self.value


class Place(Pattern):
    """
    A class representing a place pattern.

    This pattern alternates between two other patterns based on the iterator value.

    Args:
        p1 (Pattern): The first pattern to alternate between.
        p2 (Pattern): The second pattern to alternate between.

    Returns:
        The value of the first pattern if the iterator is even, otherwise the value of the second pattern.
    """

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

    def _resolve_pattern(self, pattern, iterator):
        if isinstance(pattern, Pattern):
            return pattern(iterator)
        else:
            return pattern


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


class Pgeom(Pattern):
    """
    A geometric pattern generator.

    This class represents a geometric pattern generator that produces a sequence of values
    based on a starting value, a common ratio, and a specified length.

    Raises:
        ValueError: If the length parameter 'len' is not specified for looping.

    Returns:
        float: The next value in the geometric sequence.
    """

    def __init__(self, start: float, ratio: float, len: Optional[int] = None):
        super().__init__()
        self.start = start
        self.ratio = ratio
        self.len = len

    def __call__(self, iterator):
        if self.len is None:
            raise ValueError("Length parameter 'len' must be specified for looping")

        index = iterator % self.len
        return self.start * (self.ratio**index)


class Parr(Pattern):
    """
    Represents a pattern that generates a sequence of values based on a start value, step size, and length.

    Args:
        start (float): The starting value of the pattern.
        step (float): The step size between each value in the pattern.
        len (Optional[int]): The length of the pattern. If not specified, the pattern will loop indefinitely.

    Returns:
        float: The next value in the pattern sequence.
    """

    def __init__(self, start: float, step: float, len: Optional[int] = None):
        super().__init__()
        self.start = start
        self.step = step
        self.len = len

    def __call__(self, iterator):
        if self.len is None:
            raise ValueError("Length parameter 'len' must be specified for looping")

        index = iterator % self.len
        return self.start + index * self.step


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


# Sequence patterns


class SequencePattern: ...


class Pseq(Pattern, SequencePattern):
    def __init__(self, *values, len: Optional[int] = None, reverse: bool = False):
        super().__init__()
        self._length = len
        self._reverse = reverse
        self.values = values

    def __call__(self, iterator):
        if self._reverse:
            index = len(self.values) - 1 - iterator % len(self.values)
        else:
            index = iterator % len(self.values) if self._length is None else iterator % self._length
        return self.values[index]


class Pnote(Pseq):
    """
    Pnote class represents a pattern of musical notes.

    Args:
        *values: Variable number of values representing the notes in the pattern.
        len (int | None, optional): Length of the pattern. Defaults to None.
        reverse (bool, optional): Flag indicating whether the pattern should be reversed. Defaults to False.
        root (int | None, optional): Root note of the pattern. Defaults to None.
        scale (str | None, optional): Scale of the pattern. Defaults to None.

    Methods:
        __call__(self, iterator): Evaluates the pattern with the given iterator.

    Returns:
        int | list[int]: The evaluated note value(s) based on the pattern.

    Note:
        - The pattern can contain both individual notes and patterns of notes.
        - The evaluated note value(s) are calculated based on the root note and scale of the pattern.
    """

    def __init__(
        self,
        *values,
        len: int | None = None,
        reverse: bool = False,
        root: Optional[int] = None,
        scale: Optional[str] = None,
    ):
        super().__init__(*values, len=len, reverse=reverse)
        if root is not None:
            self._local_root = root
        if scale is not None:
            self._local_scale = scale

    def __call__(self, iterator):
        if self._reverse:
            index = len(self.values) - 1 - iterator % len(self.values)
        else:
            index = iterator % len(self.values) if self._length is None else iterator % self._length
        note = self.values[index]
        scale = SCALES[
            global_config.scale if not hasattr(self, "_local_scale") else self._local_scale
        ]
        root = self._local_root if hasattr(self, "_local_root") else global_config.root

        if isinstance(note, Pattern):  # Check if note is a Pattern instance
            note_value = note(iterator)  # Evaluate the pattern with the iterator
        else:
            note_value = note

        if isinstance(note_value, int):
            octave_shift = note_value // len(scale)
            scale_position = note_value % len(scale)
            note_value = root + scale[scale_position] + (octave_shift * 12)
            return note_value
        elif isinstance(note_value, list):
            final_notes = []
            for n in note_value:
                octave_shift = n // len(scale)
                scale_position = n % len(scale)
                note_value = root + scale[scale_position] + (octave_shift * 12)
                final_notes.append(note_value)
            return final_notes


class Psine(Pattern):
    """
    Psine is a pattern that generates values based on a sine wave.

    Args:
        freq (int | float): The frequency of the sine wave.
        min (int | float, optional): The minimum value of the generated pattern. Defaults to 0.
        max (int | float, optional): The maximum value of the generated pattern. Defaults to 1.
        phase (int | float, optional): The phase offset of the sine wave. Defaults to 0.

    Returns:
        int | float: The generated value based on the sine wave.
    """

    def __init__(
        self,
        freq: int | float,
        min: int | float = 0,
        max: int | float = 1,
        phase: int | float = 0,
    ):
        super().__init__()
        self.min = min
        self.max = max
        self.freq = freq
        self.phase = phase

    def __call__(self, _):
        return (math.sin((self.env.clock.beat + self.phase) * self.freq) + 1) / 2 * (
            self.max - self.min
        ) + self.min


class Psaw(Pattern):
    """
    Psaw is a pattern that generates a sawtooth wave.

    Args:
        freq (int | float): The frequency of the sawtooth wave.
        min (int | float, optional): The minimum value of the sawtooth wave. Defaults to 0.
        max (int | float, optional): The maximum value of the sawtooth wave. Defaults to 1.
        phase (int | float, optional): The phase offset of the sawtooth wave. Defaults to 0.
    """

    def __init__(
        self,
        freq: int | float,
        min: int | float = 0,
        max: int | float = 1,
        phase: int | float = 0,
    ):
        super().__init__()
        self.min = min
        self.max = max
        self.freq = freq
        self.phase = phase

    def __call__(self, _):
        return (self.env.clock.beat * self.freq + self.phase) % 1 * (self.max - self.min) + self.min


class Ptri(Pattern):
    """
    Ptri is a pattern that generates a triangular waveform.

    Args:
        freq (int | float): The frequency of the waveform.
        min (int | float, optional): The minimum value of the waveform. Defaults to 0.
        max (int | float, optional): The maximum value of the waveform. Defaults to 1.
        phase (int | float, optional): The phase offset of the waveform. Defaults to 0.
    """

    def __init__(
        self,
        freq: int | float,
        min: int | float = 0,
        max: int | float = 1,
        phase: int | float = 0,
    ):
        super().__init__()
        self.min = min
        self.max = max
        self.freq = freq
        self.phase = phase

    def __call__(self, _):
        return (
            2
            * abs((self.env.clock.beat * self.freq + self.phase) % 1 - 0.5)
            * (self.max - self.min)
            + self.min
        )


class Pcos(Pattern):
    """
    Pcos is a pattern that generates values based on the cosine function.

    Args:
        freq (int | float): The frequency of the pattern.
        min (int | float, optional): The minimum value of the pattern. Defaults to 0.
        max (int | float, optional): The maximum value of the pattern. Defaults to 1.
        phase (int | float, optional): The phase offset of the pattern. Defaults to 0.

    Returns:
        int | float: The generated value based on the cosine function.
    """

    def __init__(
        self,
        freq: int | float,
        min: int | float = 0,
        max: int | float = 1,
        phase: int | float = 0,
    ):
        super().__init__()
        self.min = min
        self.max = max
        self.freq = freq
        self.phase = phase

    def __call__(self, _):
        return (math.cos((self.env.clock.beat + self.phase) * self.freq) + 1) / 2 * (
            self.max - self.min
        ) + self.min


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
            result.append(pattern(iterator))
        return result


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
        if random.random() < current_factor:
            return self.pattern_b(iterator)
        else:
            return self.pattern_a(iterator)


class Pfunc(Pattern):
    """
    A class representing a pattern that applies a given function to an iterator.

    Args:
        function (callable): The function to be applied to the iterator.
    """

    def __init__(self, function: Callable | Pattern):
        super().__init__()
        self.function = function

    def _resolve_value(self, value, iterator):
        if isinstance(value, Pattern):
            return value(iterator)
        else:
            return value

    def __call__(self, iterator):
        return self.function(iterator)


class Pwchoose(Pattern):
    """
    A pattern that chooses a value from a set of values with optional weights.

    Args:
        *values: Variable number of values to choose from.
        weights (Optional[list[float]]): Optional list of weights corresponding to the values.
        If not provided, all values are equally weighted.

    Returns:
        The chosen value.
    """

    def __init__(self, *values, weights: Optional[list[float]] = None):
        super().__init__()
        self.values = values
        if weights is None:
            self.weights = [1] * len(values)
        else:
            self.weights = weights

    def __call__(self, iterator):
        resolved_weights = [w(iterator) if isinstance(w, Pattern) else w for w in self.weights]
        return random.choices(self.values, weights=resolved_weights)[0]


class Pexp(Pattern):
    """
    Represents an exponential pattern.

    Args:
        min (int | float | Pattern): The minimum value or pattern of values of the pattern.
        max (int | float | Pattern): The maximum value or pattern of values of the pattern.
        n (int | Pattern): The number of steps or pattern of steps in the pattern.
    """

    def __init__(self, min: int | float | Pattern, max: int | float | Pattern, n: int | Pattern):
        super().__init__()
        self.min = min
        self.max = max
        self.n = n

    def _get_value(
        self,
        value,
        iterator,
    ):
        if isinstance(value, Pattern):
            return value(iterator)
        else:
            return value

    def __call__(self, iterator):
        index = iterator % self.n
        min_value = self._get_value(self.min, iterator)
        max_value = self._get_value(self.max, iterator)
        n_value = self._get_value(self.n, iterator)
        return min_value * (max_value / min_value) ** (index / n_value)


class Plin(Pattern):
    """
    Represents a linear pattern that generates values between a start and end value.

    Args:
        start (int | float | Pattern): The starting value or pattern of values of the pattern.
        end (int | float | Pattern): The ending value or pattern of values of the pattern.
        n (int): The number of steps in the pattern.
    """

    def __init__(self, start: int | float | Pattern, end: int | float | Pattern, n: int):
        super().__init__()
        self.start = start
        self.end = end
        self.n = n

    def __call__(self, iterator):
        index = iterator % self.n
        if isinstance(self.start, Pattern):
            start_value = self.start(iterator)
        else:
            start_value = self.start

        if isinstance(self.end, Pattern):
            end_value = self.end(iterator)
        else:
            end_value = self.end

        return start_value + (end_value - start_value) * index / self.n


class Plog(Pattern):
    """
    Represents a Plog pattern that generates values based on a logarithmic progression.

    Args:
        start (int | float): The starting value of the pattern.
        end (int | float): The ending value of the pattern.
        n (int): The number of steps in the pattern.

    Returns:
        float: The value of the pattern at the given iterator position.
    """

    def __init__(self, start: int | float, end: int | float, n: int):
        super().__init__()
        self.start = start
        self.end = end
        self.n = n

    def __call__(self, iterator):
        index = iterator % self.n
        return self.start * (self.end / self.start) ** (index / self.n)


class Prepeat(Pattern):
    """
    A pattern that repeats a sequence of arguments.

    Args:
        *args: Variable length arguments representing the sequence of values to repeat.
        repeat (int): The number of times to repeat the sequence.

    Attributes:
        args: The sequence of values to repeat.
        repeat: The number of times to repeat the sequence.

    """

    def __init__(self, *args, repeat: int):
        super().__init__()
        self.args = args
        self.repeat = repeat

    def __call__(self, iterator):
        index = iterator // self.repeat
        return self.args[index % len(self.args)]


class Pstutter(Pattern, SequencePattern):
    def __init__(self, *values, repeat: int = 1):
        super().__init__()
        self.values = values
        self.repeat = repeat
        self.index = 0

    def __call__(self, iterator):
        index = iterator // self.repeat
        value_index = index % len(self.values)
        return self.values[value_index]
