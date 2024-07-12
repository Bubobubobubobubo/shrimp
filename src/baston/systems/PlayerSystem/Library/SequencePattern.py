from ..Pattern import Pattern
from typing import Optional, Callable, Any
import random
from ..GlobalConfig import global_config
from ..Scales import SCALES


class SequencePattern:
    def __init__(
        self,
        *values,
        length: Optional[int | Pattern] = None,
    ):
        """
        A base class for sequence patterns.

        Args:
            *values: Variable number of values to be used in the pattern.
            length (int | Pattern, optional): The length of the pattern. Defaults to None.
        """
        self._length = length
        self.values = values

    def every(self, n: int, method: Callable, *args, **kwargs):

        def _wrapped_behavior():
            current_beat = self.env.clock.beat
            if int(current_beat) % n == 0:
                # Copy of itself to avoid modifying the original pattern
                new_instance = type(self)(*self.values, length=self._length)
                result = method(new_instance, *args, **kwargs)
                print(result.values)
                return result
            else:
                return self

        return ConditionalApplicationPattern(_wrapped_behavior)

    def shuffle(self):
        """
        Shuffles the values in the sequence pattern.

        Returns:
            SequencePattern: The shuffled sequence pattern.
        """
        random.shuffle(self.values)
        return self

    def reverse(self):
        """
        Reverses the values in the sequence pattern.

        Returns:
            SequencePattern: The reversed sequence pattern.
        """
        self.values = self.values[::-1]
        return self

    def mirror(self):
        """
        Mirrors the values in the sequence pattern.

        Returns:
            SequencePattern: The mirrored sequence pattern.
        """
        self.values = self.values + self.values[-2::-1]
        return self

    def sort(self, reverse=False):
        """
        Sorts the values in the sequence pattern.

        Args:
            reverse (bool, optional): Whether to sort in reverse order. Defaults to False.

        Returns:
            SequencePattern: The sorted sequence pattern.
        """
        self.values = sorted(self.values, reverse=reverse)
        return self

    def arp(self, seq):
        """
        Applies an arpeggio pattern to the values in the sequence.

        Args:
            seq (list): The arpeggio pattern to apply.

        Returns:
            Pattern: A new Pattern object with the arpeggiated values.
        """
        new_values = []
        for value in self.values:
            for increment in seq:
                new_values.append(value + increment)
        self.values = new_values
        return self

    def lace(self, *seqs):
        """
        Laces the values of the current sequence with the values from the provided sequences.

        Args:
            *seqs: Variable number of sequences to be laced with the current sequence.

        Returns:
            self: Returns the modified SequencePattern object.

        """
        new_values = []
        max_len = max(len(self.values), *(len(seq) for seq in seqs))

        for i in range(max_len):
            if i < len(self.values):
                new_values.append(self.values[i])
            for seq in seqs:
                if i < len(seq):
                    new_values.append(seq[i])

        self.values = new_values
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
        if not self.values:
            return self  # No values to rotate
        n = len(self.values)
        positions = positions % n  # Normalize the positions
        self.values = self.values[-positions:] + self.values[:-positions]
        return self

    def stretch(self, size):
        """
        Stretch the sequence pattern by repeating its values to match the specified size.

        Args:
            size (int): The desired size of the stretched sequence pattern.

        Returns:
            SequencePattern: The stretched sequence pattern.

        """
        new_values = []
        original_len = len(self.values)
        if original_len == 0:
            return self
        for i in range(size):
            new_values.append(self.values[i % original_len])
        self.values = new_values
        return self

    def filter_repeats(self):
        """
        Filters out repeated values in the sequence pattern.

        Returns:
            SequencePattern: The filtered sequence pattern.
        """
        self.values = [self.values[0]] + [
            value for i, value in enumerate(self.values[1:]) if value != self.values[i]
        ]
        return self

    def trim(self, size):
        """
        Trims the sequence pattern to the specified size.

        Args:
            size (int): The desired size of the sequence pattern.

        Returns:
            SequencePattern: The trimmed sequence pattern.

        """
        self.values = self.values[:size]
        return self

    def ltrim(self, size):
        """
        Trims the left side of the sequence pattern by removing elements from the beginning.

        Args:
            size (int): The number of elements to remove from the beginning of the sequence pattern.

        Returns:
            SequencePattern: The modified sequence pattern object.

        """
        self.values = self.values[-size:]
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
        if isinstance(n, list):
            new_values = []
            for i, value in enumerate(self.values):
                if i < len(n):
                    new_values.extend([value] * n[i])
                else:
                    new_values.append(value)
            self.values = new_values
        else:
            self.values = [ele for ele in self.values for _ in range(n)]
        return self

    def _resolve_pattern(self, pattern, iterator):
        if isinstance(pattern, Pattern):
            return pattern(iterator)
        return pattern

    def __call__(self, iterator):
        return self._resolve_pattern(self.values[iterator % len(self.values)], iterator)


class Pseq(Pattern, SequencePattern):
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
        return len(self.values)


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
