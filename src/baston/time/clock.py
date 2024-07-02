from dataclasses import dataclass, field
import uuid
import traceback
from ..utils import info_message
from ..environment import Subscriber
from typing import Any, Callable, Dict, Optional
from types import LambdaType
from time import sleep, perf_counter
import threading
import link
import types

Number = int | float


@dataclass(order=True)
class PriorityEvent:
    name: str
    priority: int | float
    item: Any = field(compare=False)
    has_played: bool = False
    passthrough: bool = False
    once: bool = False


class Clock(Subscriber):

    def __init__(self, tempo: Number, grain: Number = 0.1):
        super().__init__()
        self._clock_thread: threading.Thread | None = None
        self._stop_event: threading.Event = threading.Event()
        self._children: Dict[str, PriorityEvent] = {}
        self._playing: bool = True
        self._link = link.Link(tempo)
        self._link.enabled = True
        self._link.startStopSyncEnabled = True
        self._nominator = 4
        self._denominator = 4
        self._beat = 0
        self._bar = 0
        self._phase = 0
        self._grain = grain
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
        self.link.startStopSyncEnabled = bool

    @property
    def children(self):
        """Return the children of the clock"""
        return self._children

    @property
    def grain(self) -> Number:
        """Return the grain of the clock"""
        self._grain

    @property
    def time(self) -> Number:
        """Return the time of the clock"""
        return self._link.clock().micros() / 1000000

    @grain.setter
    def grain(self, value: Number):
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
    def tempo(self, value: Number):
        """Set the tempo of the clock"""
        if self._link:
            session = self._link.captureSessionState()
            session.setTempo(value, self._link.clock().micros())
            self._link.commitSessionState(session)

    @property
    def bar(self) -> Number:
        """Get the bar of the clock"""
        return self._bar

    @property
    def next_bar(self) -> Number:
        """Return the time position of the next bar"""
        return self.beat + self.beats_until_next_bar()

    @property
    def beat(self) -> Number:
        """Get the beat of the clock"""
        return self._beat

    @property
    def next_beat(self) -> Number:
        """Return the time position of the next beat"""
        return self.beat + 1

    @property
    def now(self) -> Number:
        """Return the time position of the current beat"""
        return self.beat

    @property
    def beat_duration(self) -> Number:
        """Get the duration of a beat"""
        return 60 / self._tempo

    @property
    def bar_duration(self) -> Number:
        """Get the duration of a bar"""
        return self.beat_duration * self._denominator

    @property
    def phase(self) -> Number:
        """Get the phase of the clock"""
        return self._phase

    def start(self) -> None:
        """Start the clock"""
        self.env.dispatch(self, "start", {})
        if not self._clock_thread:
            self._clock_thread = threading.Thread(target=self.run, daemon=False)
            self._clock_thread.start()

    def play(self, now: bool = False) -> None:
        """Play the clock"""
        if self._playing:
            return

        def _on_time_callback():
            self.env.dispatch(self, "play", {})
            session = self._link.captureSessionState()
            self._playing = True
            session.setIsPlaying(True, self._link.clock().micros())
            self._link.commitSessionState(session)

        if now:
            _on_time_callback()
        else:
            self.add(func=_on_time_callback, time=self.next_bar, once=True, passthrough=True)

    def pause(self) -> None:
        """Pause the clock"""
        if not self._playing:
            return
        self.env.dispatch(self, "pause", {})
        session = self._link.captureSessionState()
        self._playing = False
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
        self.env.dispatch(self, "stop", {})
        del self._link

    def _capture_link_info(self) -> None:
        """Utility function to capture timing information from Link Session."""
        link_state = self._link.captureSessionState()
        link_time = self._link.clock().micros()
        isPlaying = link_state.isPlaying()

        if isPlaying and not self._playing:
            self._playing = True

        if not isPlaying and self._playing:
            self._playing = False

        self._beat, self._phase, self._tempo = (
            link_state.beatAtTime(link_time, self._denominator),
            link_state.phaseAtTime(link_time, self._denominator),
            link_state.tempo(),
        )
        self._bar = self._beat / self._denominator

    def run(self) -> None:
        """Clock Event Loop."""
        previous_time = perf_counter()
        while not self._stop_event.is_set():
            current_time = perf_counter()
            elapsed_time = current_time - previous_time
            self._capture_link_info()
            try:
                self._execute_due_functions()
            except Exception as e:
                print(e)
            sleep_time = self._grain - elapsed_time
            if sleep_time > 0:
                sleep(sleep_time)
            previous_time = current_time

    def _execute_due_functions(self) -> None:
        """Execute all functions that are due to be executed."""
        possible_callables = sorted(self._children.values(), key=lambda event: event.priority)

        for callable in possible_callables:
            if callable.priority <= self._beat and not callable.has_played:
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
        return self._denominator - self._beat % self._denominator

    def add(
        self,
        func: Callable,
        time: Optional[int | float] = None,
        resolution: Optional[int | float] = 0.01,
        name: Optional[str] = None,
        relative: bool = False,
        once: bool = False,
        passthrough: bool = False,
        *args,
        **kwargs,
    ):
        """Add any Callable to the clock.

        Args:
            func (Callable): The function to be executed.
            time (int|float, optional): The beat at which the event
            should be executed. Defaults to clock.beat + 1.
            once (bool, optional): If True, the function will only be executed once.

        Returns:
            None
        """
        if time:
            if isinstance(time, (Callable, LambdaType)):
                while isinstance(time, (Callable | LambdaType)):
                    time = time()
            if relative:
                time = self.beat + (1 if time is None else time)
            else:
                time = time if time is not None else self.beat + 1

        resolution = resolution if resolution else self._grain
        time = round(time / resolution) * resolution

        # NOTE: experimental, trying to assign a name to registered functions
        if not name:
            if isinstance(func, Callable) and func.__name__ != "<lambda>":
                func_name = func.__name__
            else:
                func_name = str(uuid.uuid4())
        else:
            func_name = name

        if func_name in self._children:
            self._children[func_name].priority = time
            self._children[func_name].item = (func, args, kwargs)
            self._children[func_name].has_played = False
        else:
            # Extract priority from the time argument
            self._children[func_name] = PriorityEvent(
                name=func_name,
                priority=time,
                once=once,
                passthrough=passthrough,
                has_played=False,
                item=(func, args, kwargs),
            )

    def clear(self) -> None:
        """Clear all events from the clock."""
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
