from ...environment import Subscriber
from dataclasses import dataclass
from typing import TypeVar, Callable, ParamSpec, Optional, Dict, Self, Any, List
from ...time.clock import Clock, TimePos
from types import LambdaType
from .Pattern import Pattern
from .Rest import Rest
from .Library.TimePattern import TimePattern
from dataclasses import dataclass
import traceback

P = ParamSpec("P")
T = TypeVar("T")

__ALL__ = ["PlayerPattern", "Player"]


@dataclass
class PlayerPattern:
    send_method: Callable[P, T]  # type: ignore
    args: tuple[Any]
    kwargs: dict[str, Any]
    manual_polyphony: bool = False
    iterations: int = 0
    limit: Optional[int] = None


class Player(Subscriber):
    """Player class to manage short musical patterns and play them on the clock."""

    def __init__(self, name: str, clock: Clock):
        super().__init__()
        self._name = name
        self._clock = clock
        self._iterator = -1
        self._silence_count = 0
        self._patterns = []
        self._current_pattern_index = 0
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
        return self._patterns[self._current_pattern_index] if self._patterns else None

    @pattern.setter
    def pattern(self, pattern: Optional[PlayerPattern]):
        """Set the current pattern"""
        if pattern is None:
            self._patterns = []
        else:
            self._patterns = [pattern]
        self._current_pattern_index = 0

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
                try:
                    return resolve_value(value())
                except TypeError:
                    return resolve_value(self.iterator - self._silence_count)
            else:
                return value

        new_kwargs = {}
        for key, value in kwargs.items():
            new_kwargs[key] = resolve_value(value)

        return new_kwargs

    def stop(self, _: dict = {}):
        self._clock.remove_by_name(self._name)
        for pattern in self._patterns:
            pattern.iterations = 0
        self._patterns = []
        self._current_pattern_index = 0
        self._iterator = -1
        self._silence_count = 0

    def play(self) -> None:
        """Play the current pattern."""
        self._push()

    def __mul__(self, patterns: Optional[PlayerPattern | List[PlayerPattern]] = None) -> None:
        def _callback(patterns):
            if patterns is None:
                self.stop()
                return

            if isinstance(patterns, PlayerPattern):
                patterns = [patterns]

            self._patterns = patterns
            self._current_pattern_index = 0
            # self._patterns[0].kwargs["quant"] = "bar"
            self._push()

        next_bar = self._clock.next_bar
        self._clock.add(
            func=lambda: _callback(patterns),
            name=f"{self._name}_pattern_start",
            time=next_bar - 0.02,
        )

    # def __mul__(self, patterns: Optional[PlayerPattern | List[PlayerPattern]] = None) -> None:
    #     if patterns is None:
    #         self.stop()
    #         return

    #     if isinstance(patterns, PlayerPattern):
    #         patterns = [patterns]

    #     self._patterns = patterns
    #     self._current_pattern_index = 0

    #     # Schedule the pattern change at the start of the next bar
    #     next_bar = self._clock.next_bar
    #     self._clock.add(func=self._push, name=f"{self._name}_pattern_start", time=next_bar)

    def _handle_manual_polyphony(self, pattern: PlayerPattern, args: tuple, kwargs: dict) -> None:
        all_lists = [arg for arg in args if isinstance(arg, list)] + [
            value for value in kwargs.values() if isinstance(value, list)
        ]
        max_length = max(len(lst) for lst in all_lists) if all_lists else 1

        for i in range(max_length):
            current_args = [arg[i % len(arg)] if isinstance(arg, list) else arg for arg in args]
            current_kwargs = {
                key: value[i % len(value)] if isinstance(value, list) else value
                for key, value in kwargs.items()
            }
            pattern.send_method(*current_args, **current_kwargs)

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
                if pattern.manual_polyphony:
                    self._handle_manual_polyphony(pattern, args, kwargs)
                else:
                    pattern.send_method(*args, **kwargs)
        except Exception as e:
            print(f"Error with {pattern.send_method}: {e}, {args}, {kwargs}")
            traceback.print_exc()

        if pattern.limit is not None and pattern.iterations >= pattern.limit:
            self._transition_to_next_pattern()
        else:
            self._push(again=True)

        # self._push(again=True)

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
        self._push(again=True)

    def _schedule_next_pattern(self):
        """Schedule the transition to the next pattern."""
        next_beat = self._clock.next_bar
        self._clock.add(
            func=self._transition_to_next_pattern,
            time=next_beat,
            name=f"{self._name}_pattern_transition",
        )

    @classmethod
    def initialize_patterns(cls, clock: Clock) -> Dict[str, Self]:
        """Initialize a vast amount of patterns for every two letter combination of letter.

        Args:
            clock (Clock): The clock object.
        """
        patterns = {}
        for i in range(20):
            name = f"p{i}"
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
        return PlayerPattern(
            send_method=send_method,
            manual_polyphony=kwargs.get("manual_polyphony", False),
            args=args,
            kwargs=kwargs,
        )

    def _push(self, again: bool = False, **kwargs) -> None:
        if not self._patterns:
            return

        current_pattern = self._patterns[self._current_pattern_index]
        schedule_silence = False

        kwargs = {
            "pattern": current_pattern,
            "passthrough": current_pattern.kwargs.get("passthrough", False),
            "once": current_pattern.kwargs.get("once", False),
            "relative": True if again else False,
            "p": lambda: current_pattern.kwargs.get("p", 1),
            "swing": current_pattern.kwargs.get("swing", 0),
        }

        while isinstance(kwargs["p"], Callable | LambdaType | Pattern):
            if isinstance(kwargs["p"], Pattern):
                kwargs["p"] = kwargs["p"](self.iterator)
            elif isinstance(kwargs["p"], Callable | LambdaType):
                kwargs["p"] = kwargs["p"]()

        if isinstance(kwargs["p"], Rest):
            kwargs["p"] = kwargs["p"].duration
            self._silence_count += 1
            schedule_silence = True

        swing = kwargs.get("swing", 0.0)
        if swing > 0:
            if self._iterator % 2 == 0:
                adjusted_duration = kwargs["p"] * (1 - swing)
            else:
                adjusted_duration = kwargs["p"] * (1 + swing)

            if schedule_silence:
                kwargs["p"] = Rest(adjusted_duration)
            else:
                kwargs["p"] = adjusted_duration

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
        else:
            kwargs["time"] = kwargs["p"]

        self._iterator += 1

        current_pattern.iterations += 1
        limit = current_pattern.kwargs.get("limit", None)
        if limit is not None and current_pattern.iterations > limit:
            self._transition_to_next_pattern()
            return

        self._clock.add(
            func=self._func if not schedule_silence else self._silence, name=self._name, **kwargs
        )

    def _transition_to_next_pattern(self):
        current_pattern = self._patterns[self._current_pattern_index]
        self._patterns[self._current_pattern_index].iterations = 0

        self._current_pattern_index = (self._current_pattern_index + 1) % len(self._patterns)

        self._iterator = -1
        self._silence_count = 0

        # Ensure the next pattern starts immediately after the current pattern's duration
        next_pattern_delay = current_pattern.kwargs.get("p", 1)
        if isinstance(next_pattern_delay, Callable | LambdaType | Pattern):
            if isinstance(next_pattern_delay, Pattern):
                next_pattern_delay = next_pattern_delay(self.iterator)
            elif isinstance(next_pattern_delay, Callable | LambdaType):
                next_pattern_delay = next_pattern_delay()

        # Adding the next pattern start immediately after the current one
        self._clock.add(func=self._push, name=self._name, relative=True, time=next_pattern_delay)
