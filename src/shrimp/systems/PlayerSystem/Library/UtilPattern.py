from ..Pattern import Pattern
from typing import Callable


class Pfunc(Pattern):
    """
    A class representing a pattern that applies a given function to an iterator.

    Args:
        function (callable): The function to be applied to the iterator.
    """

    def __init__(self, function: Callable | Pattern):
        super().__init__()
        self.function = function

    def __call__(self, iterator):
        return self.function(iterator)
