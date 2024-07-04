from ..environment import Subscriber
from dataclasses import dataclass
from typing import TypeVar, Callable, ParamSpec, Optional, Dict, Self, Any
from ..time.clock import Clock
from string import ascii_lowercase, ascii_uppercase
from itertools import product
from types import LambdaType
from .Pattern import Pattern, Rest

P = ParamSpec("P")
T = TypeVar("T")


@dataclass
class PlayerPattern:
    send_method: Callable[P, T]  # type: ignore
    args: tuple[Any]
    kwargs: dict[str, Any]


class Player(Subscriber):
    """Player class to manage short musical patterns and play them on the clock."""

    def __init__(self, name: str, clock: Clock):
        super().__init__()
        self._name = name
        self._clock = clock
        self._iterator = 0
        self._silence_count = 0
        self._pattern: Optional[PlayerPattern] = None
        self._next_pattern: Optional[PlayerPattern] = None
        self._sync_quant_policy: Optional[str] = None

        self.register_handler("all_notes_off", self.stop)

    def __repr__(self):
        return f"Player {self._name}, pattern: {self._pattern}"

    def __str__(self):
        return f"Player {self._name}, pattern: {self._pattern}"

    @property
    def iterator(self):
        """Return the current iterator"""
        return self._iterator

    @iterator.setter
    def iterator(self, value: int):
        """Set the current iterator"""
        self._iterator = value

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

    def _args_resolver(self, args: tuple[Any]) -> tuple[Any]:
        """Resolve the arguments of the pattern.

        Args:
            args (tuple): The arguments to resolve

        Returns:
            tuple: The resolved arguments
        """
        new_args = ()

        for arg in args:
            if isinstance(arg, Pattern):
                new_args += (arg(self.iterator - self._silence_count),)
            elif isinstance(arg, Callable | LambdaType):
                new_args += (arg(),)

        return new_args  # type: ignore

    def _kwargs_resolver(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Resolve the keyword arguments of the pattern.

        Args:
            kwargs (dict): The keyword arguments to resolve

        Returns:
            dict: The resolved keyword arguments
        """

        def resolve_value(value: Any) -> Any:
            if isinstance(value, Pattern):
                resolved = value(self.iterator - self._silence_count)
                return resolve_value(resolved)
            elif isinstance(value, Callable | LambdaType):
                return value()
            else:
                return value

        new_kwargs = {}
        for key, value in kwargs.items():
            new_kwargs[key] = resolve_value(value)

        return new_kwargs

    def _func(self, pattern: PlayerPattern, *args, **kwargs) -> None:
        """Internal recursive function (central piece of the machanism).
        Args:
            *args: Arguments
            pattern (PlayerPattern): The pattern to play
        """
        args = self._args_resolver(pattern.args)
        kwargs = self._kwargs_resolver(pattern.kwargs)
        try:
            self._pattern.send_method(*args, **kwargs)
        except Exception as e:
            print(e)

        self.iterator += 1
        self._push(again=True)

    def _silence(self, *args, _: Optional[PlayerPattern] = None, **kwargs) -> None:
        """Internal recursive function implementing a silence."""
        self.iterator += 1
        self._push(again=True)

    def __mul__(self, pattern: Optional[PlayerPattern] = None) -> None:
        """Push new pattern to the player.

        Args:
            pattern (Optional[PlayerPattern], optional): The pattern to push. Defaults to None.
            None will stop the current pattern and clear the pattern attribute.
        """
        was_playing_a_pattern = self._pattern is not None

        if pattern is None and was_playing_a_pattern:
            self.stop()
            return

        if was_playing_a_pattern:
            if self._next_pattern is not None:
                return
            self._next_pattern = pattern
            return

        self._pattern = pattern
        self._push()

    def _push(self, again: bool = False, **kwargs) -> None:
        """Managing the lifetime of the pattern"""
        schedule_silence = False

        if self._sync_quant_policy:
            # Reset sync quant policy after one use
            print("Changement de police")
            kwargs["quant"] = self._sync_quant_policy
            self._sync_quant_policy = None

        kwargs = {
            "pattern": self._pattern,
            "passthrough": self._pattern.kwargs.get("passthrough", False),
            "once": self._pattern.kwargs.get("once", False),
            "relative": True if again else False,
            "time": lambda: self._pattern.kwargs.get("dur", 1),
        }

        # Resolve time if it is a pattern, a callable or any complex thing
        while isinstance(kwargs["time"], Callable | LambdaType | Pattern):
            if isinstance(kwargs["time"], Pattern):
                kwargs["time"] = kwargs["time"](self.iterator)
            elif isinstance(kwargs["time"], Callable | LambdaType):
                kwargs["time"] = kwargs["time"]()

        # If time is a rest, schedule a silence and count it for other seqs
        if isinstance(kwargs["time"], Rest):
            kwargs["time"] = kwargs["time"].duration
            self._silence_count += 1
            schedule_silence = True

        # Handling pattern rescheduling!
        if not again:
            if self._sync_quant_policy is None:
                quant_policy = self._pattern.kwargs.get("quant", "bar")
            else:
                quant_policy = self._sync_quant_policy

            kwargs["time"] = self._apply_quant_policy(quant_policy)

        if self._next_pattern:

            def _change_pattern_at_bar():
                self._pattern = self._next_pattern
                self._next_pattern = None
                self._push()

            quant_policy_for_next_pattern = self._pattern.kwargs.get("quant", "bar")
            change_time = self._apply_quant_policy(quant_policy_for_next_pattern)

            self._clock.add(
                func=_change_pattern_at_bar,
                time=change_time - 0.001,
            )

        self._clock.add(
            func=self._func if not schedule_silence else self._silence,
            name=self._name,
            **kwargs,
        )

    def _apply_quant_policy(self, quant_policy: Optional[str]) -> float:
        """Apply the quantization policy to determine the next event time.

        Args:
            quant_policy (Optional[str]): The quantization policy to apply.

        Returns:
            float: The adjusted time based on the quantization policy.
        """
        if quant_policy == "bar":
            return self._clock.next_bar
        elif quant_policy == "beat":
            return self._clock.next_beat
        elif quant_policy == "now":
            return self._clock.beat
        elif isinstance(quant_policy, (int, float)):
            return self._clock.beat + quant_policy

        return self._clock.next_bar

    def stop(self, _: dict = {}):
        """Stop the current pattern."""
        self._pattern = None
        self.iterator = 0
        self._silence_count = 0
        self._clock.remove_by_name(self._name)

    def play(self) -> None:
        """Play the current pattern."""
        self._push()

    def sync(self, quant_policy: str):
        """Apply a temporary quantization policy for the next call.

        Args:
            quant_policy (str): The quantization policy to apply temporarily.
                                Can be 'bar', 'beat', 'now', or a specific duration (int or float).
        """
        if quant_policy not in ["bar", "beat", "now"] and not isinstance(
            quant_policy, (int, float)
        ):
            raise ValueError("Invalid quantization policy.")
        self._sync_quant_policy = quant_policy

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
    def _play_factory(send_method: Callable[P, T], *args, **kwargs) -> PlayerPattern:
        """Factory method to create a PlayerPattern object. This is used to create a specific
        pattern type calling a specific output method.

        Args:
            send_method (Callable[P, T]): The method to call
            *args: Arguments
            **kwargs: Keyword arguments
        """
        return PlayerPattern(send_method=send_method, args=args, kwargs=kwargs)


def pattern_printer(*args, **kwargs):
    """Utility function to debug patterns"""
    print(f"{args}{kwargs}")
