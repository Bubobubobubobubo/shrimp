from ..Pattern import Pattern
from typing import Optional, Callable, Any, Self, List
import random
from ..GlobalConfig import global_config
from ..Scales import SCALES
from dataclasses import dataclass
from .SequenceTransformer import *


@dataclass
class SequenceTransformation:
    condition: Callable
    transformer: Callable

    def __repr__(self):
        return f"Condition: {self.condition}, Transformer: {self.transformer}"

    def __str__(self) -> str:
        return self.__repr__()


class SequencePattern(Pattern):
    def __init__(
        self,
        *sequence,
        length: Optional[int | Pattern] = None,
        hardness: Optional[int] = 1,
    ):
        """
        A base class for sequence patterns.

        Args:
            *values: Variable number of values to be used in the pattern.
            length (int | Pattern, optional): The length of the pattern. Defaults to None.
        """
        super().__init__()
        self._length = length
        self.sequence = sequence
        self._stack = []
        self._hardness = hardness

    def mul(self, mult: int | float) -> Self:
        self._stack.append(
            SequenceTransformation(condition=lambda: True, transformer=lambda target: mul(target))
        )
        return self

    def div(self, div: int | float) -> Self:
        self._stack.append(
            SequenceTransformation(condition=lambda: True, transformer=lambda target: div(target))
        )
        return self

    def add(self, add: int | float) -> Self:
        self._stack.append(
            SequenceTransformation(condition=lambda: True, transformer=lambda target: add(target))
        )
        return self

    def replace(self, new_seq: List[Any] | Any) -> Self:
        self._stack.append(
            SequenceTransformation(
                condition=lambda: True, transformer=lambda target: replace(target, new_seq)
            )
        )

    def every(self, n: int, method: Callable, *args, **kwargs) -> Self:
        """
        Adds a sequence transformation that applies the given method to the target
        on every nth beat of the clock.

        Args:
            n (int): The beat interval at which the method should be applied.
            method (Callable): The method to be applied to the target.
            *args: Variable length argument list to be passed to the method.
            **kwargs: Arbitrary keyword arguments to be passed to the method.

        Returns:
            self: Returns the instance of the class to allow method chaining.
        """

        self._stack.append(
            SequenceTransformation(
                condition=lambda: int(self.env.clock.beat) % n == 0,
                transformer=lambda target: method(target, *args, **kwargs),
            )
        )

        return self

    def on_beat(self, beat: int, method: Callable, *args, **kwargs) -> Self:
        """
        Adds a sequence transformation that applies the given method to the target
        on the specified beat of the clock.

        Args:
            beat (int): The beat at which the method should be applied.
            method (Callable): The method to be applied to the target.
            *args: Variable length argument list to be passed to the method.
            **kwargs: Arbitrary keyword arguments to be passed to the method.

        Returns:
            self: Returns the instance of the class to allow method chaining.
        """

        self._stack.append(
            SequenceTransformation(
                condition=lambda: int(self.env.clock.beat) % self.env._clock._denominator == beat,
                transformer=lambda target: method(target, *args, **kwargs),
            )
        )

        return self

    def on_bar(self, bar: int, cycle: int, method: Callable, *args, **kwargs) -> Self:
        """
        Adds a sequence transformation that applies the given method to the target
        on the specified beat of the clock.

        Args:
            beat (int): The beat at which the method should be applied.
            method (Callable): The method to be applied to the target.
            *args: Variable length argument list to be passed to the method.
            **kwargs: Arbitrary keyword arguments to be passed to the method.

        Returns:
            self: Returns the instance of the class to allow method chaining.
        """

        self._stack.append(
            SequenceTransformation(
                condition=lambda: self.env.clock.bar % cycle == bar,
                transformer=lambda target: method(target, *args, **kwargs),
            )
        )

        return self

    def first_of(self, n: int, cycle: int, method: Callable, *args, **kwargs) -> Self:
        """
        Adds a sequence transformation that applies the given method to the target
        on the first 'n' bars of a cycle of 'cycle' bars.

        Args:
            n (int): The number of bars during which the transformation will be applied
            cycles (int): The number of bars to create a period
            method (Callable): The method to be applied to the target.
            *args: Variable length argument list to be passed to the method.
            **kwargs: Arbitrary keyword arguments to be passed to the method.

        Returns:
            self: Returns the instance of the class to allow method chaining.
        """

        def _condition():
            current_bar = self.env.clock.bar % cycle
            return current_bar in list(range(0, n))

        self._stack.append(
            SequenceTransformation(
                condition=lambda: _condition(),
                transformer=lambda target: method(target, *args, **kwargs),
            )
        )

        return self

    def last_of(self, n: int, cycle: int, method: Callable, *args, **kwargs) -> Self:
        """
        Adds a sequence transformation that applies the given method to the target
        on the last 'n' bars of a cycle of 'cycle' bars.

        Args:
            n (int): The number of bars during which the transformation will be applied
            cycles (int): The number of bars to create a period
            method (Callable): The method to be applied to the target.
            *args: Variable length argument list to be passed to the method.
            **kwargs: Arbitrary keyword arguments to be passed to the method.

        Returns:
            self: Returns the instance of the class to allow method chaining.
        """

        def _condition():
            current_bar = self.env.clock.bar % cycle
            bars = [cycle - i for i in range(0, n + 1)]
            return current_bar in bars

        self._stack.append(
            SequenceTransformation(
                condition=lambda: _condition(),
                transformer=lambda target: method(target, *args, **kwargs),
            )
        )
        return self

    def cond(self, condition: Callable, method: Callable, *args, **kwargs) -> Self:
        """
        Adds a sequence transformation that applies the given method to the target
        if the condition is met.

        Args:
            condition (Callable): The condition that determines whether the method should be applied.
            method (Callable): The method to be applied to the target.
            *args: Variable length argument list to be passed to the method.
            **kwargs: Arbitrary keyword arguments to be passed to the method.

        Returns:
            self: Returns the instance of the class to allow method chaining.
        """

        self._stack.append(
            SequenceTransformation(
                condition=condition,
                transformer=lambda target: method(target, *args, **kwargs),
            )
        )

        return self

    def stack(self, sequence) -> Self:
        """
        Stacks the values of the current sequence with the values from the provided sequences.

        Args:
            *seqs: Variable number of sequences to stack with the current sequence.

        Returns:
            self: The current instance of the SequencePattern
        """
        self._stack.append(
            SequenceTransformation(
                condition=lambda: True,
                transformer=lambda target: stack(target, sequence),
            )
        )

        return self

    def shuffle(self, condition=lambda: True) -> Self:
        """
        Shuffles the sequence of the target.

        Args:
            condition: A callable that determines whether the shuffle should be applied.
                       If the condition returns True, the shuffle will be applied.
                       If the condition returns False, the shuffle will be skipped.
                       Defaults to lambda: True.

        Returns:
            self: The current instance of the SequencePattern object.

        """

        def _shuffle_sequence(target):
            random.shuffle(target)
            return target

        self._stack.append(
            SequenceTransformation(
                condition=condition,
                transformer=lambda target: _shuffle_sequence(target),
            )
        )

        return self

    def reverse(self, condition=lambda: True) -> Self:
        """
        Reverses the sequence of the target.

        Args:
            condition: A callable that determines whether the reverse should be applied.
                       If the condition returns True, the reverse will be applied.
                       If the condition returns False, the reverse will be skipped.
                       Defaults to lambda: True.

        Returns:
            self: The current instance of the SequencePattern object.
        """

        self._stack.append(
            SequenceTransformation(
                condition=condition,
                transformer=lambda target: target[::-1],
            )
        )

        return self

    def mirror(self, condition: Callable = lambda: True) -> Self:
        """
        Mirrors the sequence of the target.

        Args:
            condition: A callable that determines whether the mirror should be applied.
                       If the condition returns True, the mirror will be applied.
                       If the condition returns False, the mirror will be skipped.
                       Defaults to lambda: True.

        Returns:
            self: The current instance of the SequencePattern
        """

        self._stack.append(
            SequenceTransformation(
                condition=condition,
                transformer=lambda target: target + target[-2::-1],
            )
        )

        return self

    def sort(self, reverse=False, condition=lambda: True) -> Self:
        """
        Sorts the values of the current sequence.

        Args:
            reverse (bool, optional): If True, sorts the values in reverse order. Defaults to False.
            condition: A callable that determines whether the sort should be applied.
                       If the condition returns True, the sort will be applied.
                       If the condition returns False, the sort will be skipped.
                       Defaults to lambda: True.

        Returns:
            self: The current instance of the SequencePattern
        """

        self._stack.append(
            SequenceTransformation(
                condition=condition,
                transformer=lambda target: sorted(target, reverse=reverse),
            )
        )

        return self

    def arp(self, seq, condition=lambda: True) -> Self:
        """
        Applies an arpeggiator to the values of the current sequence.

        Args:
            seq (list): The sequence of intervals to be applied to the values.
            condition: A callable that determines whether the arpeggiator should be applied.
                       If the condition returns True, the arpeggiator will be applied.
                       If the condition returns False, the arpeggiator will be skipped.
                       Defaults to lambda: True.

        Returns:
            self: The current instance of the SequencePattern
        """
        self._stack.append(
            SequenceTransformation(
                condition=condition,
                transformer=lambda target: arp(target, seq),
            )
        )

        return self

    def rotate(self, positions) -> Self:
        """
        Rotates the values in the SequencePattern by the specified number of positions.

        Args:
            positions (int): The number of positions to rotate the values. Positive
            values rotate to the right, while negative values rotate to the left.

        Returns:
            SequencePattern: The SequencePattern object after the rotation.

        """
        self._stack.append(
            SequenceTransformation(
                condition=lambda: True,
                transformer=lambda target: rotate(target, positions),
            )
        )
        return self

    def stretch(self, size) -> Self:
        """
        Stretch the sequence pattern by repeating its values to match the specified size.

        Args:
            size (int): The desired size of the stretched sequence pattern.

        Returns:
            SequencePattern: The stretched sequence pattern.

        """
        self._stack.append(
            SequenceTransformation(
                condition=lambda: True,
                transformer=lambda target: stretch(target, size),
            )
        )
        return self

    def filter_repeats(self) -> Self:
        """
        Filters out repeated values in the sequence pattern.

        Returns:
            SequencePattern: The filtered sequence pattern.
        """
        self._stack.append(
            SequenceTransformation(
                condition=lambda: True,
                transformer=lambda target: filter_repeats(target),
            )
        )
        return self

    def trim(self, size) -> Self:
        """
        Trims the sequence pattern to the specified size.

        Args:
            size (int): The desired size of the sequence pattern.

        Returns:
            SequencePattern: The trimmed sequence pattern.

        """
        self._stack.append(
            SequenceTransformation(
                condition=lambda: True, transformer=lambda target: trim(target, size)
            )
        )
        return self

    def ltrim(self, size) -> Self:
        """
        Trims the left side of the sequence pattern by removing elements from the beginning.

        Args:
            size (int): The number of elements to remove from the beginning of the sequence pattern.

        Returns:
            SequencePattern: The modified sequence pattern object.

        """
        self._stack.append(
            SequenceTransformation(
                condition=lambda: True,
                transformer=lambda target: ltrim(target, size),
            )
        )
        return self

    def repeat(self, n) -> Self:
        """
        Repeats the values in the sequence pattern.

        Args:
            n (int or list): The number of times to repeat each value. If `n` is an integer,
            all values in the sequence pattern will be repeated `n` times. If `n` is a list,
            each value in the sequence pattern will be repeated a different number of times
            based on the corresponding element in the list.

        Returns:
            self: The updated sequence pattern object.

        Example usage:
            pattern = SequencePattern([1, 2, 3])
            pattern.repeat(2)  # Repeats each value twice: [1, 1, 2, 2, 3, 3]
            pattern.repeat([1, 2, 3])  # Repeats each value a different number of times: [1, 2, 2, 3, 3, 3]
        """
        self._stack.append(
            SequenceTransformation(
                condition=lambda: True,
                transformer=lambda target: repeat(target, n),
            )
        )
        return self

    def _resolve_pattern(self, pattern, iterator):
        if isinstance(pattern, Pattern):
            return pattern(iterator)
        return pattern

    def __call__(self, iterator):
        """Resolving the stack and returning the good index in the final sequence"""
        solved_pattern = list(self.sequence)

        # No transformations, we just proceed to return the sequence as is
        if len(self._stack) == 0:
            index = (iterator // self._hardness) % len(solved_pattern)
            return self._resolve_pattern(self.sequence[index], iterator)

        for pattern_transformation in self._stack:

            # Each pattern transformation is a condition and a transformer
            # When the condition is true, we apply the transformation to the
            # pattern. We re-assign the sequence after each transformation
            # until the stack is depleted.

            if pattern_transformation.condition():
                solved_pattern = pattern_transformation.transformer(solved_pattern)

        index = (iterator // self._hardness) % len(solved_pattern)
        return solved_pattern[index]


class Pseq(SequencePattern):
    def __init__(
        self, *values, length: Optional[int] = None, hardness: Optional[int] = 1, **kwargs
    ):
        Pattern.__init__(self)  # Initialize the base Pattern class
        SequencePattern.__init__(
            self,
            *values,
            length=length,
            hardness=hardness,
            **kwargs,
        )

    def __call__(self, iterator):
        return SequencePattern.__call__(self, iterator)

    def __len__(self) -> int:
        return len(self.sequence)


class Pnote(SequencePattern):
    def __init__(
        self,
        *values,
        length: Optional[int] = None,
        root: Optional[int] = None,
        scale: Optional[str] = None,
        hardness: Optional[int] = 1,
        **kwargs,
    ):
        super().__init__(*values, length=length, hardness=hardness, **kwargs)
        self._root = root
        self._raw_scale = scale

    def __call__(self, iterator):
        self._local_root = self._root if self._root is not None else global_config.root
        self._scale = self._raw_scale if self._raw_scale is not None else global_config.scale
        note = super().__call__(iterator)
        root = self._local_root
        note_value = self._resolve_pattern(note, iterator) if isinstance(note, Pattern) else note

        if isinstance(note_value, int):
            return self._calculate_note(note_value, self._scale, root)
        elif isinstance(note_value, list):
            return [
                self._calculate_note(self._resolve_pattern(n, iterator), self._scale, root)
                for n in note_value
            ]

    @staticmethod
    def _calculate_note(note, scale, root):
        octave_shift = note // len(scale)
        scale_position = note % len(scale)
        return root + scale[scale_position] + (octave_shift * 12)


class ConditionalApplicationPattern(Pattern):
    def __init__(self, wrapped_pattern: Callable):
        super().__init__()
        self.condition_pattern = wrapped_pattern

    def __call__(self, iterator: int) -> Any:
        return self._resolve_pattern(self.condition_pattern(), iterator)


Pn = Pnote
P = Pseq
