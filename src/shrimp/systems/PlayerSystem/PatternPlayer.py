from ...environment import Subscriber
from dataclasses import dataclass
from typing import TypeVar, Callable, ParamSpec, Optional, Dict, Self, Any, List
from ...time.Clock import Clock, TimePos
from types import LambdaType, GeneratorType
from inspect import isgeneratorfunction
from .Pattern import Pattern
from .Rest import Rest
from .Library.TimePattern import TimePattern
from dataclasses import dataclass
import traceback
from inspect import isgeneratorfunction, isgenerator
from collections.abc import Iterable
import logging


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
        self._patterns = None
        self._speed = 1
        self._current_pattern_index = 0
        self._next_pattern: Optional[Sender] = None
        self._transition_scheduled = False
        self._until: Optional[int] = None
        self._active: bool = True

        # Registering handlers
        self.register_handler("all_notes_off", self.stop)
        self.register_handler("children_reset", lambda _: self._react_to_play_event())

    def __repr__(self):
        return f"Player {self._name}, pattern: {self._patterns}"

    def __str__(self):
        return f"Player {self._name}, pattern: {self._patterns}"

    def __rshift__(self, *args, **kwargs) -> None:
        self._update_pattern(*args, **kwargs)

    @property
    def active(self):
        """Return the active state of the player."""
        return self._active

    @property
    def current_pattern(self):
        """Return the current pattern."""
        if self._patterns:
            try:
                return self._patterns[self._current_pattern_index]
            except IndexError:
                return self._patterns[0]
        else:
            raise ValueError("This player has no pattern.")

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
        """Return the value of a key in the current pattern."""
        return self.pattern.kwargs.get(key, None)

    def _react_to_play_event(self, *args, **kwargs):
        """React to the play event. This method is called when the "play" event is triggered."""
        # Reset the iterator and iterations on sender
        if self.pattern is not None:
            self.pattern.iterations = 0
        self.iterator = -1
        self._silence_count = 0

    # Argument and keyword argument resolvers

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
        self._patterns = None
        self._current_pattern_index = 0
        self._iterator = -1
        self._silence_count = 0

    def play(self) -> None:
        """Play the current pattern."""
        self._push()

    def _update_pattern(self, patterns: Optional[Sender | List[Sender]] = None) -> None:
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
        if patterns is None:
            logging.info(f"(Player) {self._name} stopping at {round(self._clock.beat, 2)}.")
            self.stop()
            return

        if isinstance(patterns, list):
            quant = patterns[0].kwargs.get("quant", False)
            begin = patterns[0].kwargs.get("begin", False)
        else:
            quant = patterns.kwargs.get("quant", False)
            begin = patterns.kwargs.get("begin", False)

        is_an_update = self._patterns is not None

        def _callback(reset_iterator: bool = False):
            if quant:
                logging.info(f"============= QUANT EVAL ===============")
            else:
                logging.info(f"============= EVAL ===============")
            if reset_iterator:
                self._iterator, self._silence_count = -1, 0
                self._patterns = [patterns] if isinstance(patterns, Sender) else patterns
                self.current_pattern.iterations = 0
            else:
                current_pattern_iteration = self.current_pattern.iterations if self._patterns else 0
                self._patterns = [patterns] if isinstance(patterns, Sender) else patterns
                self.current_pattern.iterations = current_pattern_iteration

        if self._name in self._clock._events:
            if quant:
                self._clock._events[self._name].next_time = int(self._clock.now) + quant
                _callback(reset_iterator=True)
            else:
                _callback()
        else:
            logging.info(f"(Player) {self._name} starting at {round(self._clock.beat, 2)}.")
            self._patterns = [patterns] if isinstance(patterns, Sender) else patterns
            time_reference = int(self._clock.next_bar) if begin is False else begin
            logging.warning(f"Time Reference: {time_reference}")
            self._clock.add(
                name=self._name,
                func=lambda: self._push(first_time=True),
                time_reference=time_reference,
                time=0,
                once=False,
                passthrough=False,
            )

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
        args = self._args_resolver(pattern.args)
        kwargs = self._kwargs_resolver(pattern.kwargs)
        self._speed = kwargs.get("speed", 1)
        end = kwargs.get("end", False)
        if end:
            if self._clock.now >= end:
                logging.info(f"End time reached for {self._name}.")
                self.stop()
                return

        # Until condition: stop the pattern after n iterations
        if pattern.kwargs.get("until", None) is not None:
            if self._iterator >= pattern.kwargs["until"]:
                self.stop()
                return

        # Grab active from kwargs
        self.active = kwargs.get("active", True)

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
            self._push()

    def _silence(self, *args, pattern: Optional[Sender] = None, **kwargs) -> None:
        """Internal recursive function implementing a silence, aka a function that do nothing.
        This is the "mirror" version of the _func method but this one doesn't do anything!

        Args:
            args (tuple): The arguments
            kwargs (dict): The keyword arguments
        """
        self._push()

    def _push(self, first_time: bool = False) -> None:
        """
        Internal method to push the pattern to the clock. This method is called recursively by the
        _func method. It schedules the next iteration of the pattern on the clock. This method is
        very complex and handles a lot of different cases.

        Args:
            again (bool): Whether the pattern is playing _again_ or not.

        Returns:
            None
        """
        # These are kwargs link to time that we should handle and process manually!
        kwargs = {
            "period": lambda: self.current_pattern.kwargs.get("period", 1),
            "nudge": self.current_pattern.kwargs.get("nudge", 0),
            "swing": self.current_pattern.kwargs.get("swing", 0),
        }

        self._resolve_period(kwargs)
        schedule_silence = self._process_silence(kwargs)
        self._handle_swing(schedule_silence, kwargs)
        self.current_pattern.limit = self.current_pattern.kwargs.get("limit", None)
        kwargs["time"] = kwargs["period"] * self._speed

        self._iterator, self.current_pattern.iterations = (
            self._iterator + 1,
            self.current_pattern.iterations + 1,
        )

        if first_time:
            player_last_deadline = self._clock._events[self._name].next_time - kwargs["period"]
        else:
            player_last_deadline = self._clock._events[self._name].next_time
        logging.info(f"Player {self._name} last deadline: {player_last_deadline}")
        self._clock.add(
            name=self._name,
            func=self._func if not schedule_silence else self._silence,
            time_reference=player_last_deadline,
            pattern=self.current_pattern,
            **kwargs,
        )

    def _resolve_period(self, kwargs):
        """Resolve the period argument."""
        while isinstance(kwargs["period"], Callable | LambdaType | Pattern):
            if isinstance(kwargs["period"], Pattern):
                kwargs["period"] = kwargs["period"](self.iterator)
            elif isinstance(kwargs["period"], Callable | LambdaType):
                kwargs["period"] = kwargs["period"]()

    def _process_silence(self, kwargs):
        """Process silence in the pattern."""
        schedule_silence = False
        if isinstance(kwargs["period"], Rest):
            kwargs["period"] = kwargs["period"].duration
            self._silence_count += 1
            schedule_silence = True
        return schedule_silence

    def _handle_swing(self, schedule_silence, kwargs):
        """Handle swing in the pattern."""
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

    def _transition_to_next_pattern(self):
        """
        Internal method to transition to the next pattern. This method is called when the current
        pattern has reached its limit. It schedules the next pattern on the clock.

        Returns:
            None
        """
        self._current_pattern_index = (self._current_pattern_index + 1) % len(self._patterns)
        self.current_pattern.iterations = 0
        self._iterator = -1
        self._silence_count = 0

        # Ensure the next pattern starts immediately after the current pattern's duration
        next_pattern_delay = self.current_pattern.kwargs.get("period", 1)
        if isinstance(next_pattern_delay, Callable | LambdaType | Pattern):
            if isinstance(next_pattern_delay, Pattern):
                next_pattern_delay = next_pattern_delay(self.iterator)
            elif isinstance(next_pattern_delay, Callable | LambdaType):
                next_pattern_delay = next_pattern_delay()

        # Adding the next pattern start immediately after the current one
        self._push(True)

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

    @classmethod
    def create_player(cls, name: str, clock: Clock) -> Self:
        """
        Initialize a single Player object. This method is used to create a single Player object
        if you need a special one or if you have overriden an instance created by default.
        """
        return Player(name=name, clock=clock)

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
            player = Player(name=name, clock=clock)
            patterns[name] = player
        for i in range(20):
            name = f"P{i}"
            player = Player(name=name, clock=clock)
            patterns[name] = player
        return patterns

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

    @staticmethod
    def __is_generator_or_iterable(arg: Any) -> bool:
        """Check if the argument is a generator or an iterable."""
        tests = [
            isgeneratorfunction(arg),
            isgenerator(arg),
            isinstance(arg, GeneratorType),
            isinstance(arg, Iterable),
        ]
        return any(tests)
