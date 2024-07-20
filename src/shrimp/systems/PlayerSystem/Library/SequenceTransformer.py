from dataclasses import dataclass
from typing import List, Any, Callable
import random


@dataclass
class SequenceTransformation:
    """Transformations to apply to a sequence in a SequencePattern."""

    condition: Callable
    transformer: Callable

    def __repr__(self):
        return f"Condition: {self.condition}, Transformer: {self.transformer}"

    def __str__(self) -> str:
        return self.__repr__()


def replace(old_seq: List[Any] | Any, new_seq: List[Any] | Any) -> List[Any]:
    if isinstance(old_seq, (int | float)):
        old_seq = [old_seq]
    return new_seq


def add(seq, adder):
    if isinstance(seq, (int | float)):
        seq = [seq]
    return [n + adder for n in seq]


def div(seq, divisor):
    if isinstance(seq, (int | float)):
        seq = [seq]
    return [n / divisor for n in seq]


def mul(seq, multiplicator):
    if isinstance(seq, (int | float)):
        seq = [seq]
    return [n * multiplicator for n in seq]


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
        if isinstance(value, (int, float)):
            for increment in pattern:
                new_values.append(value + increment)
        else:
            for increment in pattern:
                new_values.append([v + increment for v in value])
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
    if isinstance(sequence, (int | float)):
        sequence = [sequence]
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
    if isinstance(seq, int | float):
        return [seq] * n
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
