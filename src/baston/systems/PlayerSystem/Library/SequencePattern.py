from ..Pattern import Pattern
from typing import Optional, Callable, Any
import random
from ..GlobalConfig import global_config
from ..Scales import SCALES
from dataclasses import dataclass


def arp(seq, pattern) -> list:
    """
    Pure version of the arpeggiator transformation for SequencePattern.
    This function takes a sequence and an arpeggiator pattern and returns
    a new sequence with the arpeggiator applied.

    Args:
        seq (list): The input sequence to apply the arpeggiator to.
        pattern (list): The arpeggiator pattern to apply to the sequence.

    Returns:
        list: The new sequence with the arpeggiator applied.
    """
    new_values = []
    for value in seq:
        for increment in pattern:
            new_values.append(value + increment)
    return new_values


def stack(seq, sequence) -> list:
    """
    Pure version of the stack transformation for SequencePattern.
    This function takes a sequence and another sequence to stack on top of it.
    It will stack the values of the two sequences together, looping the second
    sequence if it is shorter than the first.

    Args:
        seq (list): The input sequence to stack values on top of.
        sequence (list): The sequence to stack on top of the input sequence.

    Returns:
        list: The new sequence with the values stacked on top of each other.
    """
    return [[seq[i], sequence[i % len(sequence)]] for i in range(len(seq))]


def repeat(seq: list, n: int) -> list:
    """
    Pure version of the repeat transformation for SequencePattern.
    This function takes a sequence and repeats each value in the sequence `n` times.

    Args:
        seq (list): The input sequence to repeat values in.
        n (int): The number of times to repeat each value in the sequence.

    Returns:
        list: The new sequence with the values repeated `n` times.
    """
    if isinstance(n, list):
        new_values = []
        for i, value in enumerate(seq):
            if i < len(n):
                new_values.extend([value] * n[i])
            else:
                new_values.append(value)
        seq = new_values
    else:
        seq = [ele for ele in seq for _ in range(n)]

    return seq


def shuffle(seq) -> list:
    """
    Pure version of the shuffle transformation for SequencePattern.
    This function takes a sequence and shuffles the values in the sequence.

    Args:
        seq (list): The input sequence to shuffle.

    Returns:
        list: The new sequence with the values shuffled.
    """
    random.shuffle(seq)
    return seq


def reverse(seq) -> list:
    """
    Pure version of the reverse transformation for SequencePattern.
    This function takes a sequence and reverses the order of the values in the sequence.

    Args:
        seq (list): The input sequence to reverse.

    Returns:
        list: The new sequence with the values reversed.
    """
    return seq[::-1]


def mirror(seq) -> list:
    """
    Pure version of the mirror transformation for SequencePattern.
    This function takes a sequence and mirrors the values in the sequence.

    Args:
        seq (list): The input sequence to mirror.

    Returns:
        list: The new sequence with the values mirrored.
    """
    return seq + seq[-2::-1]


def sort(seq, reverse=False) -> list:
    """
    Pure version of the sort transformation for SequencePattern.
    This function takes a sequence and sorts the values in the sequence.

    Args:
        seq (list): The input sequence to sort.
        reverse (bool, optional): If True, sorts the values in reverse order. Defaults to False.

    Returns:
        list: The new sequence with the values sorted.
    """
    return sorted(seq, reverse=reverse)


def lace(seq, *seqs) -> list:
    """
    Pure version of the lace transformation for SequencePattern.
    This function takes a sequence and a variable number of additional sequences
    and interleaves the values of the sequences together.

    Args:
        seq (list): The input sequence to interleave values with.
        *seqs (list): Variable number of sequences to interleave with the input sequence.

    Returns:
        list: The new sequence with the values interleaved.
    """
    new_values = []
    max_len = max(len(seq), *(len(seq) for seq in seqs))

    for i in range(max_len):
        if i < len(seq):
            new_values.append(seq[i])
        for seq in seqs:
            if i < len(seq):
                new_values.append(seq[i])

    return new_values


def rotate(seq, positions) -> list:
    """
    Rotates the values in the sequence by the specified number of positions.

    Args:
        seq (list): The input sequence to rotate.
        positions (int): The number of positions to rotate the values. Positive
        values rotate to the right, while negative values rotate to the left.

    Returns:
        list: The new sequence with the values rotated.
    """
    n = len(seq)
    positions = positions % n
    return seq[-positions:] + seq[:-positions]


def stretch(seq, size) -> list:
    """
    Stretch the sequence by repeating its values to match the specified size.

    Args:
        seq (list): The input sequence to stretch.
        size (int): The desired size of the stretched sequence.

    Returns:
        list: The stretched sequence.
    """
    return [seq[i % len(seq)] for i in range(size)]


def filter_repeats(seq) -> list:
    """
    Filters out repeated values in the sequence.

    Args:
        seq (list): The input sequence to filter.

    Returns:
        list: The filtered sequence with repeated values removed.
    """
    return [seq[0]] + [value for i, value in enumerate(seq[1:]) if value != seq[i]]


def trim(seq, size) -> list:
    """
    Trims the sequence to the specified size.

    Args:
        seq (list): The input sequence to trim.
        size (int): The desired size of the sequence.

    Returns:
        list: The trimmed sequence.
    """
    return seq[:size]


def ltrim(seq, size):
    """
    Trims the left side of the sequence by removing elements from the beginning.

    Args:
        seq (list): The input sequence to trim.
        size (int): The number of elements to remove from the beginning of the sequence.

    Returns:
        list: The modified sequence object.
    """
    return seq[size:]


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

    def every(self, n: int, method: Callable, *args, **kwargs):
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

    def on_beat(self, beat: int, method: Callable, *args, **kwargs):
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

    def on_bar(self, bar: int, cycle: int, method: Callable, *args, **kwargs):
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

    def stack(self, sequence):
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

    def shuffle(self, condition=lambda: True):
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

    def reverse(self, condition=lambda: True):
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

    def mirror(self, condition: Callable = lambda: True):
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

    def sort(self, reverse=False, condition=lambda: True):
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

    def arp(self, seq, condition=lambda: True):
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

    def rotate(self, positions):
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

    def stretch(self, size):
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

    def filter_repeats(self):
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

    def trim(self, size):
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

    def ltrim(self, size):
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

    def repeat(self, n):
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
            return self._resolve_pattern(self.sequence[iterator % len(self.sequence)], iterator)

        for pattern_transformation in self._stack:

            # Each pattern transformation is a condition and a transformer
            # When the condition is true, we apply the transformation to the
            # pattern. We re-assign the sequence after each transformation
            # until the stack is depleted.

            if pattern_transformation.condition():
                solved_pattern = pattern_transformation.transformer(solved_pattern)

        return solved_pattern[iterator % len(solved_pattern)]


class Pseq(SequencePattern):
    def __init__(
        self,
        *values,
        length: Optional[int] = None,
    ):
        Pattern.__init__(self)  # Initialize the base Pattern class
        SequencePattern.__init__(
            self,
            *values,
            length=length,
        )

    def __call__(self, iterator):
        return SequencePattern.__call__(self, iterator)

    def __len__(self) -> int:
        return len(self.sequence)


class Pnote(Pseq):
    def __init__(
        self,
        *values,
        length: Optional[int] = None,
        root: Optional[int] = None,
        scale: Optional[str] = None,
    ):
        super().__init__(*values, length=length)
        self._local_root = root if root is not None else global_config.root
        self._scale = scale if scale is not None else global_config.scale

    def __call__(self, iterator):
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
