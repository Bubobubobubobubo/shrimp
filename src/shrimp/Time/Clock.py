from dataclasses import dataclass, field
import logging
import uuid
import traceback
from ..utils import info_message
from ..environment import Subscriber, Environment
from .TimePos import TimePos
from typing import Any, Callable, Dict, Optional
import types
import threading
import time as time_module
import math
import link
import types


@dataclass(order=True)
class PriorityEvent:
    """A class to represent an event to be scheduled."""

    name: str
    next_time: int | float = field(compare=True)
    start_time: int | float = field(compare=False)
    nudge: int | float = field(compare=False)
    item: Any = field(compare=False)
    has_played: bool = False
    passthrough: bool = False
    persistant: bool = False
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
        self._carousel_thread: threading.Thread | None = None
        self._carousel_clock_callback: Optional[Callable] = lambda a, b, c, d: 0.1
        self._stop_event: threading.Event = threading.Event()
        self._events: Dict[str, PriorityEvent] = {}
        self._playing: bool = True
        self._link = link.Link(tempo)
        self._link_epoch = self._link.clock().micros()
        self.env: Optional[Environment] = None
        self._link.enabled = True
        self._link.startStopSyncEnabled = True
        self._internal_time = 0.0
        self._beat, self._bar, self._phase = 0, 0, 0
        self._nominator, self._denominator = 4, 4
        self._grain = grain
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
        return self._events

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
        return self._link.captureSessionState().tempo()

    @property
    def cps(self):
        """Get the cycles per second of the clock"""
        return self._tempo / 60 / self._denominator

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
            self._clock_thread = threading.Thread(target=self.run, daemon=True)
            self._carousel_thread = threading.Thread(target=self._run_carousel, daemon=True)
            logging.info("Starting Main Clock Thread")
            self._clock_thread.start()
            logging.info("Starting Vortex Clock Thread")
            self._carousel_thread.start()

    def _reset_children_times(self) -> None:
        self.env.dispatch(self, "children_reset", {})
        for child in self._events.values():
            child.next_time = 0

    def play(self) -> None:
        """Play the clock: start the clock and update the session state to request play.
        This method cannot be called if the clock is already playing. This method will
        reset the children times and request a beat at time 0. This method will also dispatch
        a message to the environment to notify all subscribers that the clock is playing."""
        if self._playing:
            return
        session = self._link.captureSessionState()
        session.requestBeatAtTime(0, self._link.clock().micros(), self._denominator)
        session.setIsPlaying(True, self._link.clock().micros())
        self._link.commitSessionState(session)
        self._reset_children_times()

    def pause(self) -> None:
        """Pause mechanism: pause the clock and update the session state to request pause.
        This method cannot be called if the clock is already paused.

        Pausing the clock dispatches a pause event to the environment. It allows all subscribers
        to react accordingly.

        """
        if not self._playing:
            return

        session = self._link.captureSessionState()
        session.setIsPlaying(False, self._link.clock().micros())
        self._link.commitSessionState(session)
        if self.env:
            self.env.dispatch(self, "pause", {})

    def precise_wait(self, duration) -> None:
        """
        Wait for a specified duration using a combination of sleep and busy-waiting.

        Args:
            duration (float): The duration to wait in seconds.
        """
        end_time = time_module.perf_counter() + duration
        # Sleep until 1000 microseconds before target
        sleep_duration = duration - 0.001
        if sleep_duration > 0:
            time_module.sleep(sleep_duration)
        while time_module.perf_counter() < end_time:
            # Busy-wait for the remaining time
            pass

    def _stop(self, _: dict = {}) -> None:
        """Stop the clock and wait for the thread to finish

        Args:
            data (dict): Data to be passed to the event handler
        """
        self._stop_event.set()
        if self.env:
            self.env.dispatch(self, "stop", {})
        self._clock_thread.join()

    def _update_time(self):
        """
        Utility function to capture timing information from Link Session.

        Returns:
            bool: True if time has been successfully captured, False otherwise.
        """
        link_state = self._link.captureSessionState()
        self.internal_time = self._link.clock().micros()
        self._playing = link_state.isPlaying()
        self._beat, self._phase, self._tempo = (
            link_state.beatAtTime(self.internal_time, self._denominator),
            link_state.phaseAtTime(self.internal_time, self._denominator),
            link_state.tempo(),
        )
        self._bar = self._beat // self._denominator
        if not self._playing:
            self.pause()

    def _run_carousel(self):

        ticks, start = 0, self._link.clock().micros()

        while not self._stop_event.is_set():
            session, now = (self._link.captureSessionState(), self._link.clock().micros())
            if self.beat >= 0:
                wait_time = self._carousel_clock_callback(start, ticks, session, now)
                if wait_time > 0:
                    self.precise_wait(wait_time)
                ticks += 1

    def run(self) -> None:
        """Clock mechanism entry point. This method is called when the clock thread is started.
        It periodically updates the internal time representation and executes due functions.
        This function busy loops in its own thread (!!)."""

        while not self._stop_event.is_set():
            start_time = time_module.perf_counter()
            self._update_time()
            self._execute_due_functions()
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
        possible_callables = sorted(self._events.values(), key=lambda event: event.next_time)
        for callable in possible_callables:
            adjusted_time = callable.next_time + callable.nudge
            if adjusted_time <= self._beat and not callable.has_played:
                if self._playing or callable.passthrough:
                    callable.has_played = True
                    try:
                        func, args, kwargs = callable.item
                        func(*args, **kwargs)
                        if callable.once:
                            del self._events[callable.name]
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

    def add_from_timestamp(self, timestamp: float, func: Callable, *args, **kwargs) -> None:
        """
        Add a function to be executed on a specific UNIX Timestamp.

        Args:
            timestamp (float): The UNIX timestamp at which the function should be executed.
            func (Callable): The function to be executed.
            *args: Positional arguments to be passed to the function.
            **kwargs: Keyword arguments to be passed to the function.
        """
        self.add(func=func, time=timestamp, *args, **kwargs)

    def add(
        self,
        name: Optional[str] = None,
        func: Callable = lambda: None,
        time: Optional[int | float] = 0,
        nudge: Optional[int | float] = 0,
        quant: Optional[int | float] = None,
        time_reference: Optional[int | float] = 0,
        once: bool = False,
        passthrough: bool = False,
        *args,
        **kwargs,
    ) -> PriorityEvent:
        """Adding a function to the clock. It can mean two things:
        1. If the function is already in the clock, update the time and arguments.
        2. If the function is not in the clock, add it to the clock.

        Returns:
            PriorityEvent: The event that was added/modified.
        """
        while not isinstance(time, (int, float)):
            time = time()

        name = self.generate_event_name(func, name)
        method = self._update_on_scheduler if name in self._events else self._add_to_scheduler

        if quant is not None:
            quantized_time = self._calculate_quantized_time(quant)
            time_reference = quantized_time
            time = 0  # Set time to 0 as we're using the quantized time as reference

        return method(
            name=name,
            time=time,
            time_reference=time_reference,
            nudge=nudge,
            func=func,
            args=args,
            kwargs=kwargs,
            once=once,
            passthrough=passthrough,
        )

    def _calculate_quantized_time(self, quant: int | float) -> float:
        """Calculate the next quantized beat time."""
        if quant == 0:
            return self.beat
        current_beat = self._beat
        next_quantized_beat = math.ceil(current_beat / quant) * quant
        return next_quantized_beat

    def _update_on_scheduler(
        self,
        name: str,
        time: Optional[int | float],
        time_reference: Optional[int | float],
        nudge: Optional[int | float],
        func: Callable,
        args: tuple,
        kwargs: dict,
        once: bool,
        passthrough: bool,
    ) -> PriorityEvent:
        """Update an event already scheduled for execution

        Args:
            name (str): The name of the event.
            time (int | float): The time at which the event should be executed.
            time_reference (int | float): The time reference for the event.
            nudge (int | float): The nudge for the event.
            func (Callable): The function to be executed.
            args (tuple): Positional arguments to be passed to the function.
            kwargs (dict): Keyword arguments to be passed to the function.
            once (bool): Whether the event should be executed only once.
            passthrough (bool): Whether the event should be executed even if the clock is paused.

        Returns:
            PriorityEvent: The updated event.
        """
        children = self._events[name]

        if time_reference is not None:
            children.next_time = time_reference + time
        else:
            children.next_time += time

        children.item = (func, args, kwargs)
        children.has_played = False
        children.passthrough = passthrough
        children.once = once
        children.nudge = nudge
        return children

    def _add_to_scheduler(
        self,
        func: Callable,
        name: Optional[str],
        time: Optional[int | float],
        time_reference: Optional[int | float],
        nudge: Optional[int | float],
        args: tuple,
        kwargs: dict,
        once: bool,
        passthrough: bool,
    ) -> PriorityEvent:
        """Add an event to the scheduler: create a new event and add it to the scheduler.

        Args:
            name (str): The name of the event.
            func (Callable): The function to be executed.
            time (int | float): The time at which the event should be executed.
            time_reference (int | float): The time reference for the event.
            nudge (int | float): The nudge for the event.
            args (tuple): Positional arguments to be passed to the function.
            kwargs (dict): Keyword arguments to be passed to the function.
            once (bool): Whether the event should be executed only once.
            passthrough (bool): Whether the event should be executed even if the clock is paused.

        Returns:
            PriorityEvent: The event that was added.
        """
        if not name.startswith(("note_on_", "note_off_")):
            logging.info(f" {name} [ADDED]")

        if time_reference is not None:
            time = time_reference + time

        children = self._events[name] = PriorityEvent(
            name=name,
            start_time=self.now,
            next_time=time,
            nudge=nudge,
            once=once,
            passthrough=passthrough,
            has_played=False,
            item=(func, args, kwargs),
        )
        return children

    def generate_event_name(self, func: Callable, name: Optional[str] = None) -> str:
        """Generate a unique name for an event based on the function name or a custom name.

        Args:
            func (Callable): The function to generate a name for.
            name (str): A custom name for the event.
        Returns:
            str: The generated name.
        """
        not_a_lambda = isinstance(func, Callable) and func.__name__ != "<lambda>"
        func_name = name if name else func.__name__ if not_a_lambda else str(uuid.uuid1())[:8]
        return func_name

    def clear(self) -> None:
        """Clear all events currently scheduled."""
        if self.env:
            self.env.dispatch(self, "all_notes_off", {})
        # Clear all events except those who are persistant
        self._events = {k: v for k, v in self._events.items() if v.persistant}

    def remove(self, *args) -> None:
        """Remove an event from the clock."""
        args = filter(lambda x: isinstance(x, types.FunctionType | types.LambdaType), args)
        for func in args:
            if func.__name__ in self._events:
                del self._events[func.__name__]

    def remove_by_func(self, *args) -> None:
        """Remove an event from the clock from its func."""
        args = filter(lambda x: isinstance(x, types.FunctionType | types.LambdaType), args)
        to_remove = []
        for func in args:
            for name, event in self._events.items():
                if event.item[0] == func:
                    to_remove.append(name)
        for name in to_remove:
            del self._events[name]

    def remove_by_name(self, name: str) -> None:
        """Remove an event from the clock by its event name."""
        if name in self._events:
            del self._events[name]

    def time_position(self):
        """Return the time position of the clock."""
        return TimePos(self.bar, self.beat, self.phase)
