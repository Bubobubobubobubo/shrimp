from dataclasses import dataclass, field
import uuid
import traceback
from ..utils import info_message
from ..environment import Subscriber, Environment
from typing import Any, Callable, Dict, Optional
from types import LambdaType
from time import sleep
import threading
import math
import link
import types


@dataclass(order=True)
class PriorityEvent:
    name: str
    next_time: int | float = field(compare=True)
    next_ideal_time: int | float = field(compare=False)
    start_time: int | float = field(compare=False)
    item: Any = field(compare=False)
    has_played: bool = False
    passthrough: bool = False
    once: bool = False


class Clock(Subscriber):

    def __init__(self, tempo: int | float, grain: float = 0.0001):
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
        self._nudge = 0.05
        self._delay = 200
        self.register_handler("start", self.start)
        self.register_handler("play", self.play)
        self.register_handler("pause", self.pause)
        self.register_handler("stop", self.stop)
        self.register_handler("exit", self.stop)

    def __str__(self) -> str:
        state = "PLAY" if self._playing else "STOP"
        return f"Clock {state}: {self.tempo} BPM, {self.bar} bars, {self.beat} beats, {self.phase} phase."

    def __repr__(self) -> str:
        state = "PLAY" if self._playing else "STOP"
        return f"Clock {state}: {self.tempo} BPM, {self.bar} bars, {self.beat} beats, {self.phase} phase."

    def sync(self, bool: bool = True):
        """Enable or disable the sync of the clock"""
        self._link.startStopSyncEnabled = bool

    @property
    def internal_time(self):
        """Return the internal time of the clock"""
        return self._internal_time

    @internal_time.setter
    def internal_time(self, value: int | float):
        """Set the internal time of the clock"""
        microsecond_delay = self._delay * 1000
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
        return int(self.beat) + self.beats_until_next_bar()

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

    def start(self) -> None:
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

    def _reset_children_times(self) -> None:
        for child in self._children.values():
            child_phase = math.modf(child.next_time)[0]
            child_ideal_time = math.modf(child.next_ideal_time)[0]
            child.next_time = child_phase
            child.next_ideal_time = child_ideal_time

    def play(self, now: bool = False) -> None:
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

    def stop(self, _: dict = {}) -> None:
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
            self.play(now=True)
        elif not isPlaying and self._playing:
            self.pause()

    def run(self) -> None:
        """Clock Event Loop."""
        while not self._stop_event.is_set():
            start_time = self.internal_time
            self._capture_link_info()
            try:
                self._execute_due_functions()
            except Exception as e:
                print(e)
            end_time = self.internal_time
            elapsed_micros = end_time - start_time
            sleep_micros = max(0, int(self._grain * 1_000_000) - elapsed_micros)

            if sleep_micros > 0:
                sleep(sleep_micros / 1_000_000)

    def _execute_due_functions(self) -> None:
        """Execute all functions that are due to be executed."""
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
                        print(traceback.format_exc())
                        info_message(
                            f"Error in function [red]{func.__name__}[/red]: [yellow]{e}[/yellow]",
                            should_print=True,
                        )
                        pass

    def beats_until_next_bar(self):
        """Return the number of beats until the next bar."""
        return self._denominator - int(self._beat) % self._denominator

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
        """Add any Callable to the clock with improved precision."""
        # Naming the function
        if not name:
            if isinstance(func, Callable) and func.__name__ != "<lambda>":
                func_name = func.__name__
            else:
                func_name = str(uuid.uuid4())
        else:
            func_name = name

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
        """Update the children of the clock."""
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

    def add_on_next_bar(self, func: Callable, *args, **kwargs) -> None:
        """Add a function to the clock to be executed on the next bar.

        Args:
            func (Callable): The function to be executed.
            *args: Arguments to be passed to the function.
            **kwargs: Keyword arguments to be passed to the function.
        """
        self.add(func, self.next_bar, *args, **kwargs)

    def add_on_next_beat(self, func: Callable, *args, **kwargs) -> None:
        """Add a function to the clock to be executed on the next beat.

        Args:
            func (Callable): The function to be executed.
            *args: Arguments to be passed to the function.
            **kwargs: Keyword arguments to be passed to the function.
        """
        self.add(func, self.next_beat, *args, **kwargs)
