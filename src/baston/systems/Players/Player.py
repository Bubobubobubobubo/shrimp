from ...environment import Subscriber
from dataclasses import dataclass
from typing import TypeVar, Callable, ParamSpec, Optional, Dict, Self, Any
from ...time.clock import Clock, TimePos
from string import ascii_lowercase
from itertools import product
from types import LambdaType
from .Pattern import Pattern
from .Rest import Rest
from .Library.TimePattern import TimePattern
from dataclasses import dataclass

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
        self._transition_scheduled = False
        self._until: Optional[int] = None
        self._begin: Optional[TimePos] = None
        self._end: Optional[TimePos] = None
        self._active: bool = True
        self.register_handler("all_notes_off", self.stop)

    def __repr__(self):
        return f"Player {self._name}, pattern: {self._pattern}"

    def __str__(self):
        return f"Player {self._name}, pattern: {self._pattern}"

    @property
    def active(self):
        """Return the active state of the player."""
        return self._active

    @active.setter
    def active(self, value: bool):
        """Set the active state of the player."""
        self._active = value

    @property
    def begin(self):
        """Return the begin time of the player."""
        return self._begin

    @property
    def end(self):
        """Return the end time of the player."""
        return self._end

    @begin.setter
    def begin(self, value: TimePos):
        self._begin = value

    @end.setter
    def end(self, value: TimePos):
        self._end = value

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
        This method is recursive and can handle nested patterns.

        Args:
            args (tuple): The arguments

        Returns:
            tuple: The resolved arguments
        """
        new_args = ()

        for arg in args:
            if isinstance(arg, Pattern):
                new_args += (arg(self.iterator - self._silence_count),)
            elif isinstance(arg, Callable | LambdaType):
                new_args += (arg(),)
            elif isinstance(arg, TimePattern):
                new_args += (arg(self._clock.now),)

        return new_args  # type: ignore

    def _kwargs_resolver(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Resolve the keyword arguments of the pattern.
        This method is recursive and can handle nested patterns.

        Args:
            kwargs (dict): The keyword arguments of the pattern.

        Returns:
            dict: The resolved keyword
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

    def _silence(self, *args, _: Optional[PlayerPattern] = None, **kwargs) -> None:
        """Internal recursive function implementing a silence. This is the "mirror" version
        of the _func method but this one doesn't do anything! It is used to schedule a silence
        in the clock and count it for other sequences.

        TODO: There might be a bug to fix here! We are not counting for until or self._begin
        and self._end conditions. This might be a problem if we have a rest in a sequence.

        Args:
            args (tuple): The arguments
            kwargs (dict): The keyword arguments
        """
        self.iterator += 1
        self._push(again=True)

    def stop(self, _: dict = {}):
        """Stop the current pattern.

        Args:
            _: A dictionary to match the signature of the handler method.
        """
        self * None
        self._clock.remove_by_name(self._name)
        self._pattern = None
        self._next_pattern = None
        self._iterator = 0
        self._silence_count = 0
        self._transition_scheduled = False

    def play(self) -> None:
        """Play the current pattern."""
        self._push()

    @classmethod
    def initialize_patterns(cls, clock: Clock) -> Dict[str, Self]:
        """Initialize a vast amount of patterns for every two letter combination of letter.

        Args:
            clock (Clock): The clock object.
        """
        patterns = {}
        player_names = ["".join(tup) for tup in product(ascii_lowercase, repeat=2)]

        for name in player_names:
            patterns[name] = Player(name=name, clock=clock)

        return patterns

    @staticmethod
    def _play_factory(send_method: Callable[P, T], *args, **kwargs) -> PlayerPattern:
        """Factory method to create a PlayerPattern object.

        Args:
            send_method (Callable): The method to call.
            args (tuple): The arguments.
            kwargs (dict): The keyword arguments.

        Returns:
            PlayerPattern: The PlayerPattern object.
        """
        return PlayerPattern(send_method=send_method, args=args, kwargs=kwargs)

    def __mul__(self, pattern: Optional[PlayerPattern] = None) -> None:
        """Push new pattern to the player.

        Args:
            pattern (Optional[PlayerPattern]): The pattern to push to the player.
        """
        if pattern is None:
            return

        if self._pattern is None:
            self._pattern = pattern
            pattern.kwargs["quant"] = "bar"
            self._push()
        else:
            self._next_pattern = pattern
            self._schedule_next_pattern()

    def _push(self, again: bool = False, **kwargs) -> None:
        """Managing the lifetime of the pattern.

        Args:
            again (bool): If True, the pattern will be rescheduled.

        """
        if self._pattern is None and self._next_pattern is None:
            return

        current_pattern = self._pattern or self._next_pattern
        schedule_silence = False

        kwargs = {
            "pattern": current_pattern,
            "passthrough": current_pattern.kwargs.get("passthrough", False),
            "once": current_pattern.kwargs.get("once", False),
            "relative": True if again else False,
            "time": lambda: current_pattern.kwargs.get("dur", 1),
            "swing": current_pattern.kwargs.get("swing", 0),
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

        # Apply swing
        swing = kwargs.get("swing", 0.0)
        if swing > 0:
            if self._iterator % 2 == 0:
                adjusted_duration = kwargs["time"] * (1 - swing)
            else:
                adjusted_duration = kwargs["time"] * (1 + swing)

            if schedule_silence:
                kwargs["time"] = Rest(adjusted_duration)
            else:
                kwargs["time"] = adjusted_duration

        # Handling pattern rescheduling!
        if not again:
            quant_policy = current_pattern.kwargs.get("quant", "now")
            if quant_policy == "bar":
                kwargs["time"] = self._clock.next_bar
            elif quant_policy == "beat":
                kwargs["time"] = self._clock.next_beat
            elif quant_policy == "now":
                kwargs["time"] = self._clock.beat
            elif isinstance(quant_policy, (int, float)):
                kwargs["time"] = self._clock.beat + quant_policy

        self._clock.add(
            func=self._func if not schedule_silence else self._silence, name=self._name, **kwargs
        )

    def _func(self, pattern: PlayerPattern, *args, **kwargs) -> None:
        """Internal function to play the pattern. This function is called by the clock. It plays
        the pattern using the send_method + args and kwargs arguments.

        Args:
            pattern (PlayerPattern): The pattern to play.
            args (tuple): The arguments.
            kwargs (dict): The keyword arguments.
        """
        if pattern is None:
            return

        args = self._args_resolver(pattern.args)
        kwargs = self._kwargs_resolver(pattern.kwargs)

        # Until condition: stop the pattern after n iterations
        if pattern.kwargs.get("until", None) is not None:
            if self._iterator >= pattern.kwargs["until"]:
                self.stop()
                return

        ctime = self._clock.time_position()
        # End condition: stop the pattern at time t
        if self._end is not None and ctime > self._end:
            self._push(again=True)
            return
        # Begin condition: start the pattern at time t
        if self._begin is not None and ctime < self._begin:
            self._push(again=True)
            return

        # Grab active from kwargs
        self.active = kwargs.get("active", True)

        # Main function call
        try:
            if self._active:
                pattern.send_method(*args, **kwargs)
        except Exception as e:
            print(f"Error in _func: {e}")

        self._iterator += 1
        self._push(again=True)

    def _schedule_next_pattern(self):
        """Schedule the transition to the next pattern."""
        next_beat = self._clock.next_bar
        self._clock.add(
            func=self._transition_to_next_pattern,
            time=next_beat,
            name=f"{self._name}_pattern_transition",
        )

    def _transition_to_next_pattern(self):
        """Perform the transition to the next pattern."""
        if self._next_pattern:
            self._pattern = self._next_pattern
            self._next_pattern = None
            self._iterator = 0
            self._silence_count = 0
            self._push()


def pattern_printer(*args, **kwargs):
    """Utility function to debug patterns"""
    print(f"{args}{kwargs}")
