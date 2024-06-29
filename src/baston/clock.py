from dataclasses import dataclass, field
from .utils import info_message
from queue import PriorityQueue
from typing import Any, Callable, Dict
from time import sleep
import threading
import link
import types

Number = int | float

@dataclass(order=True)
class PriorityEvent:
    priority: int | float
    item: Any = field(compare=False)

class Clock():

    def __init__(self, tempo: int | float):
        self._clock_thread: threading.Thread | None = None
        self._stop_event: threading.Event = threading.Event()
        self._event_queue = PriorityQueue(maxsize=1000)
        self._scheduled_events: Dict[str, PriorityEvent] = {}
        self._isPlaying: bool = False
        self._link = link.Link(tempo)
        self._link.enabled = True
        self._link.startStopSyncEnabled = True
        self._nominator = 4
        self._denominator = 4
        self._beat = 0
        self._bar = 0
        self._phase = 0
        self._grain = 0.001

    def sync(self, bool: bool = True):
        """Enable or disable the sync of the clock"""
        self.link.startStopSyncEnabled = bool

    @property
    def grain(self) -> Number:
        """Return the grain of the clock"""
        self._grain

    @grain.setter
    def grain(self, value: Number):
        """Set the grain of the clock"""
        self._grain = value

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
    def beat(self) -> Number:
        """Get the beat of the clock"""
        return self._beat

    @property
    def phase(self) -> Number:
        """Get the phase of the clock"""
        return self._phase

    def start(self) -> None:
        """Start the clock"""
        if not self._clock_thread:
            self._clock_thread = threading.Thread(target=self.run).start()

    def play(self) -> None:
        """Play the clock"""
        session = self._link.captureSessionState()
        session.setIsPlaying(True, self._link.clock().micros())
        self._link.commitSessionState(session)

    def pause(self) -> None:
        """Pause the clock"""
        session = self._link.captureSessionState()
        session.setIsPlaying(False, self._link.clock().micros())
        self._link.commitSessionState(session)

    def stop(self) -> None:
        """Stop the clock and wait for the thread to finish"""
        self._stop_event.set()

    def _capture_link_info(self) -> None:
        """Utility function to capture timing information from Link Session."""
        link_state = self._link.captureSessionState()
        link_time = self._link.clock().micros()
        self._beat, self._phase, self._tempo = (
            link_state.beatAtTime(link_time, self._denominator),
            link_state.phaseAtTime(link_time, self._denominator),
            link_state.tempo()
        )
        self._bar = self._beat / self._denominator
        self._isPlaying = link_state.isPlaying

    def run(self) -> None:
        """Clock Event Loop."""
        while not self._stop_event.is_set():
            self._capture_link_info()
            self._execute_due_events()
            sleep(self._grain)

    def _execute_due_events(self):
        """Execute all due events."""
        while not self._event_queue.empty():
            event = self._event_queue.queue[0]
            if event.priority <= self._beat:
                self._event_queue.get()
                event.item()
                self._scheduled_events.pop(event.item.__name__, None)
            else:
                break

    def beats_until_next_bar(self):
        """Return the number of beats until the next bar."""
        return self._denominator - self._beat % self._denominator

    def add(self, func: Callable, time: int | float = None):
        """Add an event to the clock.

        Args:
            func (Callable): The function to be executed.
            time (int|float, optional): The beat at which the event should be executed. Defaults to clock.beat + 1.
            
        Returns:
            None
        """
        if time is None:
            time = self.beat + 1

        func_name = func.__name__
        is_lambda = isinstance(func, types.LambdaType) and func.__name__ == '<lambda>'
        
        if func_name in self._scheduled_events:
            if not is_lambda:
                info_message(f"Updating function [yellow]{func_name}[/yellow]")
            self.remove(func)

        event = PriorityEvent(priority=time, item=func)
        self._event_queue.put(event)
        self._scheduled_events[func_name] = event
        if not is_lambda:
            info_message(f"Added function [green]{func_name}[/green] at beat {time}")

    def clear(self) -> None:
        """Clear all events from the clock."""
        self._event_queue = PriorityQueue(maxsize=1000)
        self._scheduled_events = {}
        info_message("Cleared all scheduled events")

    def remove(self, func: Callable) -> None:
        """Remove an event from the clock."""
        func_name = func.__name__
        is_lambda = isinstance(func, types.LambdaType) and func.__name__ == '<lambda>'
        
        if func_name in self._scheduled_events:
            event = self._scheduled_events.pop(func_name)
            temp_queue = PriorityQueue(maxsize=1000)
            while not self._event_queue.empty():
                current_event = self._event_queue.get()
                if current_event.item != func:
                    temp_queue.put(current_event)
            self._event_queue = temp_queue
            if not is_lambda:
                info_message(f"Removed function [red]{func_name}[/red]")
        else:
            if not is_lambda:
                info_message(f"Function [red]{func_name}[/red] not found")

    def next_bar(self) -> Number:
        """Return the time position of the next bar"""
        return self.beat + self.beats_until_next_bar()