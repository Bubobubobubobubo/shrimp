from ..environment import Subscriber
from dataclasses import dataclass
from typing import TypeVar, Callable, ParamSpec, Optional, Dict, Self, Any
from ..time.clock import Clock
from string import ascii_lowercase, ascii_uppercase
from itertools import product

P = ParamSpec("P")
T = TypeVar("T")


@dataclass
class PlayerPattern:
    send_method: Callable[P, T]
    args: tuple[Any]
    kwargs: dict[str, Any]


class Player(Subscriber):

    def __init__(self, name: str, clock: Clock = None):
        super().__init__()
        self._name = name
        self._clock = clock
        self._pattern: Optional[PlayerPattern] = None

    def __repr__(self):
        return f"Player {self._name}, pattern: {self._pattern}"

    def __str__(self):
        return f"Player {self._name}, pattern: {self._pattern}"

    @property
    def pattern(self):
        """Return the current pattern"""
        return self._pattern

    @pattern.setter
    def pattern(self, pattern: Optional[PlayerPattern]):
        """Set the current pattern"""
        self._pattern = pattern

    @property
    def name(self):
        """Return the name of the player"""
        return self._name

    def _func(self, *args, pattern: Optional[PlayerPattern] = None, **kwargs) -> None:
        """Internal recursive function.
        Args:
            *args: Arguments
            pattern (PlayerPattern): The pattern to play

        Note: this is the central piece of the player system. This player system abstracts
        away the need to manage recursive functions manually.
        """
        self._pattern.send_method(*pattern.args, **pattern.kwargs)
        self._push_again()

    def __mul__(self, pattern: Optional[PlayerPattern] = None) -> None:
        """Push new pattern to the player.

        Args:
            pattern (Optional[PlayerPattern], optional): The pattern to push. Defaults to None.
            None will stop the current pattern and clear the pattern attribute.
        """
        if self._pattern is not None:
            if pattern is not None:
                self._pattern = pattern
            else:
                self.stop()
        else:
            if pattern is not None:
                quant_policy = pattern.kwargs.get("quant_policy", None)
                self._pattern = pattern
                self._push(quant_policy)

    def _push(self, quant_policy: str | int | float) -> None:
        """Managing the lifetime of the pattern

        Args:
            quant_policy (str | int | float): The quantization policy for the pattern (first launch)
        """
        kwargs = {
            "pattern": self._pattern,
            "passthrough": self._pattern.kwargs.get("passthrough", False),
            "once": self._pattern.kwargs.get("once", False),
            "relative": True,
            "time": self._pattern.kwargs.get("dur", 1),
        }

        if quant_policy == "bar":
            self._clock.add_on_next_bar(func=self._func, name=self._name, **kwargs)
        elif quant_policy == "beat":
            self._clock.add_on_next_beat(func=self._func, name=self._name, **kwargs)
        elif quant_policy in ["now", None]:
            self._clock.add(func=self._func, name=self._name, **kwargs)
        elif isinstance(quant_policy, (int, float)):
            self._clock.add(func=self._func, name=self._name, **kwargs)

    def stop(self):
        """Stop the current pattern."""
        self._pattern = None
        self._clock.remove_by_name(self._name)

    def _push_again(self) -> None:
        """Same but without the quant policy"""
        self._push(quant_policy=None)

    @classmethod
    def initialize_patterns(cls, clock: Clock) -> Dict[str, Self]:
        """Initialize a vast amount of patterns for every two letter combination of letter.
        Store them in a dictionary with the two letter combination as key.

        Args:
            clock (Clock): The clock object to use for the pattern

        Returns:
            dict: A dictionary with the two letter combination as key and the pattern as value
        """
        patterns = {}

        # Iterate over all two letter combinations
        player_names = [
            "".join(tup) for tup in product(ascii_lowercase + ascii_uppercase, repeat=2)
        ]

        for name in player_names:
            patterns[name] = Player(name=name, clock=clock)

        return patterns

    @staticmethod
    def _play_factory(send_method: Callable[P, T], *args, **kwargs) -> None:
        """Factory method to create a PlayerPattern object. This is used to create a specific
        pattern type calling a specific output method.

        Args:
            send_method (Callable[P, T]): The method to call
            *args: Arguments
            **kwargs: Keyword arguments
        """
        return PlayerPattern(send_method=send_method, args=args, kwargs=kwargs)
