from dataclasses import dataclass, field
import uuid
import traceback
from ..utils import info_message
from ..environment import Subscriber, Environment
from typing import Any, Callable, Dict, Optional
from types import LambdaType
from time import sleep
import threading
import time as time_module
import math
import link
import types


@dataclass
class TimePos:
    """A class to represent a time position in a musical context."""

    bar: int = 1
    beat: int = 0
    phase: float = 0

    def __eq__(self, other):
        if not isinstance(other, TimePos):
            return NotImplemented
        return (self.bar, self.beat, self.phase) == (other.bar, other.beat, other.phase)

    def __lt__(self, other):
        if not isinstance(other, TimePos):
            return NotImplemented
        return (self.bar, self.beat, self.phase) < (other.bar, other.beat, other.phase)

    def __le__(self, other):
        if not isinstance(other, TimePos):
            return NotImplemented
        return (self.bar, self.beat, self.phase) <= (other.bar, other.beat, other.phase)

    def __gt__(self, other):
        if not isinstance(other, TimePos):
            return NotImplemented
        return (self.bar, self.beat, self.phase) > (other.bar, other.beat, other.phase)

    def __ge__(self, other):
        if not isinstance(other, TimePos):
            return NotImplemented
        return (self.bar, self.beat, self.phase) >= (other.bar, other.beat, other.phase)

    def __eq__(self, other):
        if not isinstance(other, TimePos):
            return NotImplemented
        return (self.bar, self.beat, self.phase) == (other.bar, other.beat, other.phase)

    def __lt__(self, other):
        if not isinstance(other, TimePos):
            return NotImplemented
        return (self.bar, self.beat, self.phase) < (other.bar, other.beat, other.phase)

    def __le__(self, other):
        if not isinstance(other, TimePos):
            return NotImplemented
        return (self.bar, self.beat, self.phase) <= (other.bar, other.beat, other.phase)

    def __gt__(self, other):
        if not isinstance(other, TimePos):
            return NotImplemented
        return (self.bar, self.beat, self.phase) > (other.bar, other.beat, other.phase)

    def __ge__(self, other):
        if not isinstance(other, TimePos):
            return NotImplemented
        return (self.bar, self.beat, self.phase) >= (other.bar, other.beat, other.phase)


@dataclass(order=True)
class PriorityEvent:
    """A class to represent an event to be scheduled."""

    name: str
    next_time: int | float = field(compare=True)
    next_ideal_time: int | float = field(compare=False)
    start_time: int | float = field(compare=False)
    item: Any = field(compare=False)
    has_played: bool = False
    passthrough: bool = False
    once: bool = False


class Clock(Subscriber):
    """
    A musical clock synchronized with Ableton Link. The clock can be used to schedule events with high precision.
    Timing information is extracted from the Link session. Event scheduling is done using the central `add` method.
    Threads are used to ensure that the clock runs in the background and does not block the main thread.
    """

    def __init__(self, tempo: int | float, grain: float = 0.0001, delay: int = 0):
        super().__init__()
        self._clock_thread: threading.Thread | None = None
        self._stop_event: threading.Event = threading.Event()
        self._children: Dict[str, PriorityEvent] = {}
        self._playing: bool = True
        self._link = link.Link(tempo)
        self.env: Optional[Environment] = None
        self._link.enabled = True
        self._link.startStopSyncEnabled = True
        self._internal_time = 0.0
        self._beat, self._bar, self._phase = 0, 0, 0
        self._nominator, self._denominator = 4, 4
        self._grain = grain
        self._nudge = 0.00
        self._delay = delay
        self.register_handler("start", self._start)
        self.register_handler("play", self.play)
        self.register_handler("pause", self.pause)
        self.register_handler("stop", self._stop)
        self.register_handler("exit", self._stop)

    def __str__(self) -> str:
        state = "PLAY" if self._playing else "STOP"
        return f"Clock {state}: {self.tempo} BPM, {self.bar} bars, {self.beat} beats, {self.phase} phase."

    def __repr__(self) -> str:
        state = "PLAY" if self._playing else "STOP"
        return f"Clock {state}: {self.tempo} BPM, {self.bar} bars, {self.beat} beats, {self.phase} phase."

    def sync(self, value: bool = True):
        """Enable or disable the sync of the clock"""
        self._link.startStopSyncEnabled = value

    @property
    def peers(self) -> int:
        """Return the peers of the clock"""
        if self._link:
            return self._link.numPeers()
        else:
            return 0

    @property
    def delay(self):
        """Return the delay of the clock"""
        return self._delay

    @delay.setter
    def delay(self, value: int):
        """Set the delay of the clock"""
        if not isinstance(value, int):
            raise ValueError("Delay must be an integer")
        self._delay = value

    @property
    def internal_time(self):
        """Return the internal time of the clock"""
        return self._internal_time

    @internal_time.setter
    def internal_time(self, value: int | float):
        """Set the internal time of the clock"""
        microsecond_delay = self._delay * 10000
        self._internal_time = value - microsecond_delay

    @property
    def children(self):
        """Return the children of the clock"""
        return self._children

    @property
    def nudge(self) -> float:
        """Return the nudge of the clock"""
        for child in self._children.values():
            child.next_time += self._nudge
            child.next_ideal_time += self._nudge
        return self._nudge

    @nudge.setter
    def nudge(self, value: float):
        """Set the nudge of the clock"""
        self._nudge = value

    @property
    def grain(self) -> float:
        """Return the grain of the clock"""
        return self._grain

    @property
    def time(self) -> int | float:
        """Return the time of the clock"""
        microsecond_delay = self._delay * 1000
        return (self._link.clock().micros() - microsecond_delay) / 1000000

    @grain.setter
    def grain(self, value: int | float):
        """Set the grain of the clock"""
        self._grain = value

    @property
    def time_signature(self) -> tuple[int, int]:
        """Return the time signature of the clock"""
        return self._nominator, self._denominator

    @time_signature.setter
    def time_signature(self, value: tuple[int, int]):
        """Set the time signature of the clock"""
        self._nominator, self._denominator = value

    @property
    def tempo(self):
        """Get the tempo of the clock"""
        return self._tempo

    @tempo.setter
    def tempo(self, value: int | float):
        """Set the tempo of the clock"""
        if self._link:
            session = self._link.captureSessionState()
            session.setTempo(value, self._link.clock().micros())
            self._link.commitSessionState(session)

    @property
    def bar(self) -> int | float:
        """Get the current bar number."""
        return math.floor(self.beat / self._denominator)

    @property
    def next_bar(self) -> int | float:
        """Return the time position of the next bar"""
        return self.now + self.beats_until_next_bar(as_int=False)

    @property
    def beat(self) -> int | float:
        """Get the current beat number from Link."""
        return self._beat

    @property
    def next_beat(self) -> int | float:
        """Return the time position of the next beat"""
        return int(self.beat) + 1

    @property
    def now(self) -> int | float:
        """Return the time position of the current beat"""
        return self.beat

    @property
    def beat_duration(self) -> int | float:
        """Get the duration of a beat"""
        return 60 / self._tempo

    @property
    def bar_duration(self) -> int | float:
        """Get the duration of a bar"""
        return self.beat_duration * self._denominator

    @property
    def phase(self) -> int | float:
        """Get the current phase from Link."""
        state = self._link.captureSessionState()
        time = self._link.clock().micros()
        return state.phaseAtTime(time, self._denominator)

    def _start(self) -> None:
        """Start the clock"""
        if self.env:
            self.env.dispatch(self, "start", {})
        if not self._clock_thread:
            self._clock_thread = threading.Thread(target=self.run, daemon=False)
            self._clock_thread.start()

    def _shift_children_times(self, shift: int | float) -> None:
        """Shift all children times by a given amount."""
        for child in self._children.values():
            child.next_time += shift

    # def _reset_children_times(self) -> None:
    #     for child in self._children.values():
    #         child_phase = math.modf(child.next_time)[0]
    #         child_ideal_time = math.modf(child.next_ideal_time)[0]
    #         child.next_time = child_phase
    #         child.next_ideal_time = child_ideal_time

    def _reset_children_times(self) -> None:
        self.env.dispatch(self, "children_reset", {})
        for child in self._children.values():
            child.next_time = 0
            child.next_ideal_time = 0

    def play(self) -> None:
        """Play the clock"""
        if self._playing:
            return
        self._reset_children_times()
        session = self._link.captureSessionState()
        session.setIsPlaying(True, self._link.clock().micros())
        self._link.commitSessionState(session)
        session.requestBeatAtTime(0, self._link.clock().micros(), self._denominator)
        self._link.commitSessionState(session)
        self._playing = True

    def pause(self) -> None:
        """Pause the clock"""
        if not self._playing:
            return
        else:
            self._playing = False
            if self.env:
                self.env.dispatch(self, "pause", {})
            session = self._link.captureSessionState()
            session.setIsPlaying(False, self._link.clock().micros())
            self._link.commitSessionState(session)

    def precise_wait(self, duration) -> None:
        """
        Wait for a specified duration using a combination of sleep and busy-waiting.

        Args:
            duration (float): The duration to wait in seconds.
        """
        end_time = time_module.perf_counter() + duration
        sleep_duration = duration - 0.001  # Sleep until 1000 microseconds before target
        if sleep_duration > 0:
            time_module.sleep(sleep_duration)
        while time_module.perf_counter() < end_time:
            pass  # Busy-wait for the remaining time

    def _stop(self, _: dict = {}) -> None:
        """Stop the clock and wait for the thread to finish

        Args:
            data (dict): Data to be passed to the event handler
        """
        self._link.startStopSyncEnabled = False
        self._stop_event.set()
        self._link.enabled = False
        if self.env:
            self.env.dispatch(self, "stop", {})
        del self._link

    def _capture_link_info(self) -> None:
        """Utility function to capture timing information from Link Session."""
        link_state = self._link.captureSessionState()
        self.internal_time = self._link.clock().micros()
        isPlaying = link_state.isPlaying()
        self._beat, self._phase, self._tempo = (
            link_state.beatAtTime(self.internal_time, self._denominator),
            link_state.phaseAtTime(self.internal_time, self._denominator),
            link_state.tempo(),
        )
        self._bar = self._beat // self._denominator
        if isPlaying and not self._playing:
            self.add(
                func=lambda: self.play(),
                time=self.now - self.next_bar,
                once=True,
                passthrough=True,
                relative=False,
            )
            # self.play()
        elif not isPlaying and self._playing:
            self.pause()

    def run(self) -> None:
        """Main Clock Event Loop"""

        while not self._stop_event.is_set():
            start_time = time_module.perf_counter()
            self._capture_link_info()
            try:
                self._execute_due_functions()
            except Exception as e:
                print(e)

            end_time = time_module.perf_counter()
            elapsed_time = end_time - start_time
            wait_time = max(0, self._grain - elapsed_time)

            if wait_time > 0:
                self.precise_wait(wait_time)

    def _execute_due_functions(self) -> None:
        """Execute all functions that are due to be executed.

        This method iterates over the possible callables and executes them if they are due to be executed.
        A callable is considered due if its `next_time` attribute is less than or equal to the current beat
        and it has not been played before.

        If the clock is playing or the callable has the `passthrough` attribute set to True, the callable
        is played and marked as played. If the callable has the `once` attribute set to True, it is removed
        from the list of children after being played.

        If an exception occurs during the execution of a callable, an error message is printed along with
        the traceback.

        Returns:
            None
        """
        possible_callables = sorted(self._children.values(), key=lambda event: event.next_time)
        for callable in possible_callables:
            if callable.next_time <= self._beat and not callable.has_played:
                if self._playing or callable.passthrough:
                    callable.has_played = True
                    try:
                        func, args, kwargs = callable.item
                        func(*args, **kwargs)
                        if callable.once:
                            del self._children[callable.name]
                    except Exception as e:
                        info_message(
                            f"Error in function [red]{func.__name__}[/red]: [yellow]{e}[/yellow]",
                            should_print=True,
                        )
                        print(traceback.format_exc())
                        pass

    def beats_until_next_bar(self, as_int: bool = True) -> int | float:
        """Return the number of beats until the next bar."""
        if as_int:
            return self._denominator - int(self._beat) % self._denominator
        else:
            return self._denominator - self._beat % self._denominator

    def beats_until_next_beat(self, as_int: bool = True) -> int | float:
        """Return the number of beats until the next beat."""
        if as_int:
            return 1 - int(self._beat) % 1
        else:
            return 1 - self._beat % 1

    def add(
        self,
        func: Callable,
        time: Optional[int | float] = None,
        start_time: Optional[int | float] = None,
        name: Optional[str] = None,
        relative: bool = False,
        once: bool = False,
        passthrough: bool = False,
        *args,
        **kwargs,
    ) -> PriorityEvent:
        """
        Add a function to the clock's schedule.

        Parameters:
        - func: The function to be scheduled.
        - time: The time at which the function should be executed. If None, the function will be executed immediately.
                It can also be a Callable that returns the time dynamically.
        - start_time: The time at which the function should start. If None, the current time will be used.
        - name: The name of the function. If None, a unique identifier will be generated.
        - relative: If True, the time parameter will be treated as a relative time from the current time.
                    If False, the time parameter will be treated as an absolute time.
        - once: If True, the function will be executed only once. If False, the function will be executed repeatedly.
        - passthrough: If True, the function will execute even if the clock is paused.
        - args: Additional positional arguments to be passed to the function.
        - kwargs: Additional keyword arguments to be passed to the function.

        Returns:
        - PriorityEvent: An object representing the scheduled function.
        """
        # Naming the function
        if not name:
            if isinstance(func, Callable) and func.__name__ != "<lambda>":
                func_name = func.__name__
            else:
                func_name = str(uuid.uuid4())
        else:
            func_name = name

        if time is None:
            next_time = self.now
            ideal_time = self.now
        if time:
            # Time can be a Callable
            if isinstance(time, (Callable, LambdaType)):
                while isinstance(time, (Callable | LambdaType)):
                    time = time()

            # Relative time calculation
            if relative:
                next_time = self.now + (1 if time is None else time)
                ideal_time = 1 if time is None else time

            # Absolute time calculation
            if not relative:
                next_time = time
                ideal_time = time
        else:
            next_time = self.now
            ideal_time = self.now

        if func_name in self._children:
            children = self._update_children(
                name=func_name,
                item=(func, args, kwargs),
                next_time=next_time,
                ideal_time=ideal_time,
                relative=relative,
            )
            return children

        children = self._children[func_name] = PriorityEvent(
            name=func_name,
            next_time=next_time - self._nudge,
            next_ideal_time=next_time - self._nudge,
            once=once,
            passthrough=passthrough,
            has_played=False,
            start_time=start_time if start_time else self.now,
            item=(func, args, kwargs),
        )
        return children

    def _update_children(
        self,
        name: str,
        item: Any,
        next_time: int | float,
        ideal_time: int | float,
        relative: bool = False,
    ) -> PriorityEvent:
        """Update the children of the clock.

        Args:
            name (str): The name of the clock.
            item (Any): The item to update.
            next_time (int | float): The next time for the event.
            ideal_time (int | float): The ideal next time for the event.
            relative (bool, optional): Whether the update is relative to current time or not. Defaults to False.

        Returns:
            PriorityEvent: The updated children of the clock.
        """
        children = self._children[name]
        if relative:
            next_ideal_time: int | float = children.next_ideal_time + ideal_time
            children.next_time = next_ideal_time
            children.next_ideal_time = next_ideal_time
            children.item = item
            children.has_played = False
        if not relative:
            children.next_time = next_time
            children.next_ideal_time = ideal_time
            children.item = item
            children.has_played = False
        return children

    def clear(self) -> None:
        """Clear all events from the clock."""
        if self.env:
            self.env.dispatch(self, "all_notes_off", {})
        self._children = {}

    def remove(self, *args) -> None:
        """Remove an event from the clock."""
        args = filter(lambda x: isinstance(x, types.FunctionType | types.LambdaType), args)
        for func in args:
            if func.__name__ in self._children:
                del self._children[func.__name__]

    def remove_by_name(self, name: str) -> None:
        """Remove an event from the clock by name."""
        if name in self._children:
            del self._children[name]

    def time_position(self):
        """Return the time position of the clock."""
        return TimePos(self.bar, self.beat, self.phase)
