from ..Pattern import Pattern


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
