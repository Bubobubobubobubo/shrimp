from ..Pattern import Pattern
from typing import Optional
import itertools
import random
from ..GlobalConfig import global_config
from ..Scales import SCALES


class SequencePattern:
    def __init__(
        self,
        *values,
        length: Optional[int | Pattern] = None,
        reverse: bool | Pattern = False,
        shuffle: bool | Pattern = False,
        repeat: Optional[int | Pattern] = None,
        invert: Optional[int | Pattern] = None,
    ):
        """
        A base class for sequence patterns.

        Args:
            *values: Variable number of values to be used in the pattern.
            length (int | Pattern, optional): The length of the pattern. Defaults to None.
            reverse (bool | Pattern, optional): Whether to reverse the pattern. Defaults to False.
            shuffle (bool | Pattern, optional): Whether to shuffle the pattern. Defaults to False.
            repeat (int | Pattern, optional): The number of times to repeat the pattern. Defaults to False.
            invert (int | Pattern, optional): The value to subtract from each pattern value. Defaults to False.
        """
        self._length = length
        self._reverse = reverse
        self._shuffle = shuffle
        self._invert = invert
        self._repeat = repeat
        self._original_values = values
        self.values = list(values)

    def _repeat_values(self, values, repeat, iterator):
        expanded_values = []
        if not isinstance(repeat, Pattern):
            expanded_values = list(
                itertools.chain.from_iterable(itertools.repeat(x, repeat) for x in values)
            )
        else:
            repeat_value = repeat(iterator)
            expanded_values = list(
                itertools.chain.from_iterable(itertools.repeat(x, repeat_value) for x in values)
            )
        return expanded_values

    def _resolve_pattern(self, pattern, iterator):
        if isinstance(pattern, Pattern):
            return pattern(iterator)
        return pattern

    def __call__(self, iterator):
        # Use the original values for computation
        self.values = list(self._original_values)

        if self._repeat is not None:
            self.values = self._repeat_values(self.values, self._repeat, iterator)

        if isinstance(self._shuffle, Pattern):
            shuffle = self._resolve_pattern(self._shuffle, iterator)
        else:
            shuffle = self._shuffle

        if shuffle:
            random.shuffle(self.values)

        if isinstance(self._reverse, Pattern):
            reverse = self._resolve_pattern(self._reverse, iterator)
        else:
            reverse = self._reverse

        if reverse:
            index = len(self.values) - 1 - iterator % len(self.values)
        else:
            index = iterator % len(self.values) if self._length is None else iterator % self._length

        value = self.values[index]

        if self._invert is not None:
            if isinstance(self._invert, Pattern):
                invert = self._resolve_pattern(self._invert, iterator)
            else:
                invert = self._invert
            value -= invert
        return value


class Pseq(Pattern, SequencePattern):
    def __init__(
        self,
        *values,
        length: Optional[int] = None,
        reverse: bool = False,
        shuffle: bool = False,
        repeat: Optional[int] = None,
        invert: Optional[int] = None,
    ):
        Pattern.__init__(self)  # Initialize the base Pattern class
        SequencePattern.__init__(
            self,
            *values,
            length=length,
            reverse=reverse,
            shuffle=shuffle,
            invert=invert,
            repeat=repeat,
        )

    def __call__(self, iterator):
        return SequencePattern.__call__(self, iterator)

    def __len__(self) -> int:
        return len(self.values)


P = Pseq


class Pnote(Pseq):
    def __init__(
        self,
        *values,
        length: Optional[int] = None,
        reverse: bool = False,
        shuffle: bool = False,
        invert: Optional[int] = None,
        repeat: Optional[int] = None,
        root: Optional[int] = None,
        scale: Optional[str] = None,
    ):
        super().__init__(
            *values, length=length, reverse=reverse, shuffle=shuffle, invert=invert, repeat=repeat
        )
        self._local_root = root if root is not None else global_config.root
        self._scale = scale if scale is not None else global_config.scale

    def __call__(self, iterator):
        note = super().__call__(iterator)
        root = self._local_root
        note_value = self._resolve_pattern(note, iterator) if isinstance(note, Pattern) else note

        if isinstance(note_value, int):
            return self._calculate_note(note_value, self._scale, root)
        elif isinstance(note_value, list):
            return [self._calculate_note(n, self._scale, root) for n in note_value]

    @staticmethod
    def _calculate_note(note, scale, root):
        octave_shift = note // len(scale)
        scale_position = note % len(scale)
        return root + scale[scale_position] + (octave_shift * 12)


Pn = Pnote
