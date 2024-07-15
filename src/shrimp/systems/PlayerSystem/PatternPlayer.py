from ...environment import Subscriber
from dataclasses import dataclass
from typing import TypeVar, Callable, ParamSpec, Optional, Dict, Self, Any, List
from ...time.clock import Clock, TimePos
from types import LambdaType, GeneratorType
from inspect import isgeneratorfunction
from .Pattern import Pattern
from .Rest import Rest
from .Library.TimePattern import TimePattern
from dataclasses import dataclass
import traceback
from inspect import isgeneratorfunction, isgenerator
from collections.abc import Iterable


P = ParamSpec("P")
T = TypeVar("T")


@dataclass
class Sender:
    """
    PlayerPattern class to store the pattern information. Every pattern is a PlayerPattern object.
    """

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
        self._next_pattern: Optional[Sender] = None
        self._transition_scheduled = False
        self._until: Optional[int] = None
        self._active: bool = True
        self.register_handler("all_notes_off", self.stop)

    def __repr__(self):
        return f"Player {self._name}, pattern: {self._patterns}"

    def __str__(self):
        return f"Player {self._name}, pattern: {self._patterns}"

    # Properties

    @property
    def active(self):
        """Return the active state of the player."""
        return self._active

    @property
    def iterator(self):
        """Return the current iterator"""
        return self._iterator

    @property
    def pattern(self):
        """Return the current pattern"""
        return self._patterns[self._current_pattern_index] if self._patterns else None

    @property
    def name(self):
        """Return the name of the player"""
        return self._name

    # Setters

    @active.setter
    def active(self, value: bool):
        """Set the active state of the player."""
        self._active = value

    @iterator.setter
    def iterator(self, value: int):
        """Set the current iterator"""
        self._iterator = value

    @pattern.setter
    def pattern(self, pattern: Optional[Sender]):
        """Set the current pattern"""
        if pattern is None:
            self._patterns = []
        else:
            self._patterns = [pattern]
        self._current_pattern_index = 0

    def key(self, key):
        return self.pattern.kwargs.get(key, None)

    # Argument and keyword argument resolvers

    def __is_generator_or_iterable(self, arg: Any) -> bool:
        """Check if the argument is a generator or an iterable."""
        tests = [
            isgeneratorfunction(arg),
            isgenerator(arg),
            isinstance(arg, GeneratorType),
            isinstance(arg, Iterable),
        ]
        return any(tests)

    def _args_resolver(self, args: tuple[Any]) -> tuple[Any]:
        """Resolve pattern arguments. Each pattern is submitted along with *args and **kwargs.
        These arguments can be of many different types, including Patterns, Callables, and plain
        values. This method resolves the arguments recursively in order to feed a valid argument
        to the PlayerPattern send_method.

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
            elif isinstance(arg, (list, tuple)):
                new_args += (arg,)
            elif self.__is_generator_or_iterable(arg):
                new_args += (next(arg),)

        return new_args  # type: ignore

    def _kwargs_resolver(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Resolve pattern keyword arguments. This method is recursive and can handle nested patterns.
        Each pattern is submitted along with *args and **kwargs. These arguments can be of many different
        types, including Patterns, Callables, and plain values. This method resolves the keyword arguments
        recursively to ensure all values are fully resolved.

        Args:
            kwargs (dict): The keyword arguments of the pattern.

        Returns:
            dict: The fully resolved keyword arguments
        """

        def resolve_value(value: Any) -> Any:
            """Resolve a value recursively."""
            if isinstance(value, Pattern):
                return resolve_value(value(self.iterator - self._silence_count))
            elif isinstance(value, (list, tuple)):
                return [resolve_value(item) for item in value]
            elif isinstance(value, dict):
                return {k: resolve_value(v) for k, v in value.items()}
            elif self.__is_generator_or_iterable(value):
                return resolve_value(next(value))
            elif isinstance(value, Callable | LambdaType):
                try:
                    return resolve_value(value())
                except TypeError:
                    return resolve_value(value(self.iterator - self._silence_count))
            else:
                return value

        return {key: resolve_value(value) for key, value in kwargs.items()}

    # def _kwargs_resolver(self, kwargs: dict[str, Any]) -> dict[str, Any]:
    #     """Resolve pattern keyword arguments. This method is recursive and can handle nested patterns.
    #     Each pattern is submitted along with *args and **kwargs. These arguments can be of many different
    #     types, including Patterns, Callables, and plain values. This method resolves the keyword arguments
    #     recursively in order to feed a valid argument to the PlayerPattern send_method.

    #     Args:
    #         kwargs (dict): The keyword arguments of the pattern.

    #     Returns:
    #         dict: The resolved keyword
    #     """

    #     def resolve_value(value: Any) -> Any:
    #         """Resolve a keyword argument recursively."""
    #         if isinstance(value, Pattern):
    #             resolved = value(self.iterator - self._silence_count)
    #             return resolve_value(resolved)
    #         elif isinstance(value, (list, tuple)):
    #             return value
    #         elif self.__is_generator_or_iterable(value):
    #             return next(value)
    #         elif isinstance(value, Callable | LambdaType):
    #             try:
    #                 return resolve_value(value())
    #             except TypeError:
    #                 return resolve_value(self.iterator - self._silence_count)
    #         else:
    #             return value

    #     new_kwargs = {}
    #     for key, value in kwargs.items():
    #         new_kwargs[key] = resolve_value(value)

    #     return new_kwargs

    def stop(self, _: dict = {}):
        """Method to stop a player.

        Args:
            _: dict: The dictionary of arguments.

        Returns:
            None

        Note: This method is also used as a callback for the "all_notes_off" event.
        This is why the _ argument is present and needed, even though we do not use
        it here.
        """
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

    def __rshift__(self, patterns: Optional[Sender | List[Sender]] = None) -> None:
        """
        Central method to submit and play a pattern. This method is overriding the * operator.
        Patterns can be submitted as a single PlayerPattern object or as a list of PlayerPattern
        objects. If a list is submitted, patterns will be played in sequence, each of them lasting
        for "limit" iterations.

        You can also submit a None value to stop the player. This is equivalent to calling the stop()
        method.

        Args:
            patterns (PlayerPattern | List[PlayerPattern]): The pattern(s) to play.

        Returns:
            None
        """

        def _callback(patterns):
            if patterns is None:
                self.stop()
                return

            # TODO: do something about iterations
            if isinstance(patterns, Sender):
                patterns = [patterns]
                self._patterns = patterns
            elif isinstance(patterns, list):
                self._patterns = patterns
            self._push()

        self._clock.add(
            func=lambda: _callback(patterns),
            name=f"{self._name}_pattern_start",
            relative=True,
            time=self._clock.beats_until_next_bar(as_int=False),
            once=True,
        )

    def _handle_manual_polyphony(self, pattern: Sender, args: tuple, kwargs: dict) -> None:
        """Internal function to handle polyphony manually. This method is required for scheduling
        synthesizers written with SignalFlow (Synths/ folder). In other cases, polyphony is natively
        handled by the implementation of whatever send_method is used.

        Args:
            pattern (PlayerPattern): The pattern to play.
            args (tuple): The arguments.
            kwargs (dict): The keyword arguments.

        Returns:
            None
        """
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

    def _func(self, pattern: Sender, *args, **kwargs) -> None:
        """Internal temporal recurisve function used to play patterns. This is the central piece
        of this class. This method serves to "programatically" compose a function that will then
        be scheduled on the clock for each iteration of the player. This method is recursive and
        will call itself (through _push) until the pattern is stopped.

        There is quite a large amount of logic in this method. It handles the following:

        - Iteration limits: check if the pattern has reached its limit, if so, transition
          to the next pattern.

        - Manual polyphony: handle polyphony manually if the pattern is set to manual_polyphony.
          This is required by some synthesizers written with SignalFlow.

        - Until conditions: stop the pattern after n iterations. This is useful for one shot events
          that are not meant to loop around forever.

        - Active state: check if the player is active or not. If not, do not play the pattern.


        Args:
            pattern (PlayerPattern): The pattern to play.
            args (tuple): The arguments.
            kwargs (dict): The keyword arguments.

        Returns:
            None
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

    def _silence(self, *args, pattern: Optional[Sender] = None, **kwargs) -> None:
        """Internal recursive function implementing a silence, aka a function that do nothing.
        This is the "mirror" version of the _func method but this one doesn't do anything!

        Args:
            args (tuple): The arguments
            kwargs (dict): The keyword arguments
        """
        self._push(again=True)

    @classmethod
    def initialize_patterns(cls, clock: Clock) -> Dict[str, Self]:
        """Initialize Player objects in bulk for the user to use. This function is called
        during the initialization of the PlayerSystem. The player objects are then distributed
        to the globals() dictionary so that they can be accessed directly by the user.

        Args:
            clock (Clock): The clock object.

        Returns:
            Dict[str, Self]: A dictionary of Player objects.
        """
        patterns = {}
        for i in range(20):
            name = f"p{i}"
            patterns[name] = Player(name=name, clock=clock)
        for i in range(20):
            name = f"P{i}"
            patterns[name] = Player(name=name, clock=clock)
        return patterns

    @classmethod
    def create_player(cls, name: str, clock: Clock) -> Self:
        """
        Initialize a single Player object. This method is used to create a single Player object
        if you need a special one or if you have overriden an instance created by default.
        """
        return Player(name=name, clock=clock)

    @staticmethod
    def _play_factory(send_method: Callable[P, T], *args, **kwargs) -> Sender:
        """Factory method to create a PlayerPattern object. Used to declare various instruments
        for the user. The send_method is the method that will be called when the pattern is played.
        This class is basically in charge of gracefully handling the *args and **kwargs provided to
        it!

        Args:
            send_method (Callable): The method to call.
            args (tuple): The arguments.
            kwargs (dict): The keyword arguments.

        Returns:
            PlayerPattern: The PlayerPattern object.
        """
        return Sender(
            send_method=send_method,
            manual_polyphony=kwargs.get("manual_polyphony", False),
            args=args,
            kwargs=kwargs,
        )

    def _push(self, again: bool = False, **kwargs) -> None:
        """
        Internal method to push the pattern to the clock. This method is called recursively by the
        _func method. It schedules the next iteration of the pattern on the clock. This method is
        very complex and handles a lot of different cases.

        Args:
            again (bool): Whether the pattern is playing _again_ or not.
            kwargs (dict): The keyword arguments.

        Returns:
            None
        """
        if not self._patterns:
            return

        current_pattern = self._patterns[self._current_pattern_index]
        schedule_silence = False

        kwargs = {
            "pattern": current_pattern,
            "passthrough": current_pattern.kwargs.get("passthrough", False),
            "once": current_pattern.kwargs.get("once", False),
            "relative": True if again else False,
            "period": lambda: current_pattern.kwargs.get("period", 1),
            "swing": current_pattern.kwargs.get("swing", 0),
        }

        while isinstance(kwargs["period"], Callable | LambdaType | Pattern):
            if isinstance(kwargs["period"], Pattern):
                kwargs["period"] = kwargs["period"](self.iterator)
            elif isinstance(kwargs["period"], Callable | LambdaType):
                kwargs["period"] = kwargs["period"]()

        if isinstance(kwargs["period"], Rest):
            kwargs["period"] = kwargs["period"].duration
            self._silence_count += 1
            schedule_silence = True

        swing = kwargs.get("swing", 0.0)
        if swing > 0:
            if self._iterator % 2 == 0:
                adjusted_duration = kwargs["period"] * (1 - swing)
            else:
                adjusted_duration = kwargs["period"] * (1 + swing)

            if schedule_silence:
                kwargs["period"] = Rest(adjusted_duration)
            else:
                kwargs["period"] = adjusted_duration

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
            kwargs["time"] = kwargs["period"]

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
        """
        Internal method to transition to the next pattern. This method is called when the current
        pattern has reached its limit. It schedules the next pattern on the clock.

        Returns:
            None
        """
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
        self._clock.add(
            func=self._push,
            name=self._name,
            relative=False,
            time=round(self._clock.now, 1) + next_pattern_delay,
        )
