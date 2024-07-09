from typing import Any, List
from ..Pattern import Pattern
from itertools import zip_longest
from typing import Callable
import math
import random


class TimePattern(Pattern):
    def __init__(self):
        super().__init__()

    def __len__(self):
        return 1


class Pdur(Pattern):
    """
    Pdur is a class that represents a time-based pattern.

    Args:
        values (List[Any]): A list of values.
        durations (List[int | float]): A list of durations corresponding to each value.

    Returns:
        Any: The value corresponding to the current time.
    """

    def __init__(self, values: List[Any], durations: List[int | float], bar: bool = False):
        super().__init__()
        self._bar = bar
        self._time_tuple = list(zip_longest(values, durations, fillvalue=None))

    def __call__(self, _):
        current_time = self.env.clock.bar if self._bar else self.env.clock.beat
        filtered_time_tuple = [
            (value, duration) for value, duration in self._time_tuple if duration is not None
        ]
        total_duration = sum(duration for _, duration in filtered_time_tuple)
        position = current_time % total_duration
        accumulated_duration = 0
        for value, duration in filtered_time_tuple:
            accumulated_duration += duration
            if position < accumulated_duration:
                return value
        return None


class Psine(TimePattern):
    """
    Psine is a pattern that generates values based on a sine wave.

    Args:
        freq (int | float | Pattern): The frequency of the sine wave.
        min (int | float | Pattern, optional): The minimum value of the generated pattern. Defaults to 0.
        max (int | float | Pattern, optional): The maximum value of the generated pattern. Defaults to 1.
        phase (int | float | Pattern, optional): The phase offset of the sine wave. Defaults to 0.

    Returns:
        int | float | Pattern: The generated value based on the sine wave.
    """

    def __init__(
        self,
        freq: int | float | Pattern,
        min: int | float | Pattern = 0,
        max: int | float | Pattern = 1,
        phase: int | float | Pattern = 0,
    ):
        super().__init__()
        self.min = min
        self.max = max
        self.freq = freq
        self.phase = phase

    def __call__(self, _):
        freq = self._resolve_pattern(self.freq, self.env.clock.beat)
        min_val = self._resolve_pattern(self.min, self.env.clock.beat)
        max_val = self._resolve_pattern(self.max, self.env.clock.beat)
        phase_val = self._resolve_pattern(self.phase, self.env.clock.beat)
        return (math.sin((self.env.clock.beat + phase_val) * freq) + 1) / 2 * (
            max_val - min_val
        ) + min_val


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


class _Pinterp(Pattern):
    """
    Pinterp is a class that represents a time-based pattern with interpolation between values.

    Args:
        values (List[Any]): A list of values to interpolate between.
        durations (List[int | float]): A list of durations corresponding to each interpolation period.
        interpolation_func (Callable): A function that defines the interpolation method.
        bar (bool): If True, use bar time instead of beat time.

    Returns:
        Any: The interpolated value corresponding to the current time.
    """

    def __init__(
        self,
        values: List[Any],
        durations: List[int | float],
        interpolation_func: Callable[[float, Any, Any], Any],
        bar: bool = False,
    ):
        super().__init__()
        self._bar = bar
        self._time_tuple = list(zip_longest(values, durations, fillvalue=None))
        self._interpolation_func = interpolation_func

    def __call__(self, _):
        current_time = self.env.clock.bar if self._bar else self.env.clock.beat
        filtered_time_tuple = [
            (value, duration) for value, duration in self._time_tuple if duration is not None
        ]
        total_duration = sum(duration for _, duration in filtered_time_tuple)
        position = current_time % total_duration

        accumulated_duration = 0
        for i, (value, duration) in enumerate(filtered_time_tuple):
            if position < accumulated_duration + duration:
                progress = (position - accumulated_duration) / duration
                next_value = filtered_time_tuple[(i + 1) % len(filtered_time_tuple)][0]
                return self._interpolation_func(progress, value, next_value)
            accumulated_duration += duration

        return None


def linear_interp(progress: float, start: float, end: float) -> float:
    return start + progress * (end - start)


def exponential_interp(progress: float, start: float, end: float) -> float:
    return start * (end / start) ** progress


class PdurLin(_Pinterp):
    """Linear interpolation pattern"""

    def __init__(self, values: List[Any], durations: List[int | float], bar: bool = False):
        super().__init__(values, durations, linear_interp, bar)


class PdurExp(_Pinterp):
    """Exponential interpolation pattern"""

    def __init__(self, values: List[Any], durations: List[int | float], bar: bool = False):
        super().__init__(values, durations, exponential_interp, bar)


class Penv(Pattern):
    """
    Penv is a pattern that generates an envelope shape similar to ADSR (Attack, Decay, Sustain, Release).

    Args:
        attack (float): The duration of the attack phase.
        decay (float): The duration of the decay phase.
        sustain (float): The level of the sustain phase (0 to 1).
        release (float): The duration of the release phase.
        duration (float): The total duration of the envelope.
        min (float): The minimum value of the envelope output.
        max (float): The maximum value of the envelope output.

    Returns:
        float: The current value of the envelope (min to max).
    """

    def __init__(
        self,
        attack: float = 0.01,
        decay: float = 1,
        sustain: float = 0.5,
        release: float = 1,
        duration: float = 4,
        min: float = 0,
        max: float = 1,
    ):
        super().__init__()
        self.attack = attack
        self.decay = decay
        self.sustain = sustain
        self.release = release
        self.duration = duration
        self.min = min
        self.max = max

    def __call__(self, _):
        current_time = self.env.clock.beat % self.duration
        envelope_value = self._calculate_envelope_value(current_time)
        return self._scale_output(envelope_value)

    def _calculate_envelope_value(self, current_time: float) -> float:
        if current_time < self.attack:
            # Attack phase
            return current_time / self.attack
        elif current_time < self.attack + self.decay:
            # Decay phase
            decay_progress = (current_time - self.attack) / self.decay
            return 1 - (1 - self.sustain) * decay_progress
        elif current_time < self.duration - self.release:
            # Sustain phase
            return self.sustain
        else:
            # Release phase
            release_progress = (current_time - (self.duration - self.release)) / self.release
            return self.sustain * (1 - release_progress)

    def _scale_output(self, value: float) -> float:
        return self.min + value * (self.max - self.min)


class Pmorph(Pattern):
    def __init__(self, patterns: List[Pattern], durations: List[int | float]):
        super().__init__()
        if len(patterns) < 2:
            raise ValueError("Pmorph requires at least two patterns")
        if len(patterns) != len(durations):
            raise ValueError("Number of patterns must match number of durations")

        self.patterns = patterns
        self.durations = durations
        self.total_duration = sum(durations)

    def __call__(self, iterator):
        current_time = self.env.clock.beat % self.total_duration

        accumulated_time = 0
        for i in range(len(self.durations)):
            if current_time < accumulated_time + self.durations[i]:
                progress = (current_time - accumulated_time) / self.durations[i]
                pattern1 = self.patterns[i]
                pattern2 = self.patterns[(i + 1) % len(self.patterns)]

                try:
                    value1 = self._resolve_pattern(pattern1, iterator)
                    value2 = self._resolve_pattern(pattern2, iterator)
                except TypeError:
                    # If we can't resolve the patterns, return the first one's value
                    return self._resolve_pattern(pattern1, iterator)

                return self._interpolate(progress, value1, value2)

            accumulated_time += self.durations[i]

        # This should not be reached, but just in case:
        return self._resolve_pattern(self.patterns[0], iterator)

    def _interpolate(self, progress: float, value1: Any, value2: Any) -> Any:
        if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
            return value1 + progress * (value2 - value1)
        else:
            # For non-numeric types, we'll just switch at the midpoint
            return value1 if progress < 0.5 else value2

    def _resolve_pattern(self, pattern: Any, iterator: int) -> Any:
        if isinstance(pattern, Pattern):
            try:
                return pattern(iterator)
            except TypeError:
                # If the pattern call fails, return the pattern itself
                return pattern
        return pattern


class Pbrown(Pattern):
    """
    Pbrown (or Pwalk) generates a random walk pattern between specified minimum and maximum values.
    This implementation is stateless and relies only on the current time.

    Args:
        min (float): The minimum value of the walk.
        max (float): The maximum value of the walk.
        step (float): The maximum step size for each movement.
        seed (int, optional): Seed for the random number generator. Defaults to 0.

    Returns:
        float: The current value of the random walk.
    """

    def __init__(self, min: float, max: float, step: float, seed: int = 0):
        super().__init__()
        if min >= max:
            raise ValueError("min must be less than max")
        if step <= 0:
            raise ValueError("step must be positive")

        self.min = min
        self.max = max
        self.step = step
        self.seed = seed

    def __call__(self, _):
        current_time = self.env.clock.beat
        return self._get_value_at_time(current_time)

    def _get_value_at_time(self, time: float) -> float:
        random.seed(self.seed)
        current = (self.min + self.max) / 2  # Start at the middle

        # Use floor of time to get consistent steps
        for _ in range(math.floor(time)):
            delta = random.uniform(-self.step, self.step)
            current += delta
            current = max(self.min, min(self.max, current))

        return current
