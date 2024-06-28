from dataclasses import dataclass, field
from queue import PriorityQueue
from typing import Any, Callable
from time import sleep
import threading
import link

@dataclass(order=True)
class PriorityEvent:
    priority: int|float
    item: Any=field(compare=False)

class Clock():

    """
    A clock that can be used to synchronize events.

    TODO:
        - Implement a priority queue for events
        - Implement a way to pause the clock
        - Implement a way to change the time signature
    """

    def __init__(self, tempo: int | float):
        self._clock_thread: threading.Thread | None = None
        self._stop_event: threading.Event = threading.Event()
        self._event_queue = PriorityQueue(maxsize = 1000)
        self._scheduled_events = []
        self._isPlaying: bool = False
        self._link = link.Link(tempo)
        self._link.enabled = True
        self._link.startStopSyncEnabled = True
        self._nominator = 4
        self._denominator = 4
        self._beat = 0
        self._bar = 0
        self._phase = 0

    def sync(self, bool: bool = True):
        """Enable or disable the sync of the clock"""
        self.link.startStopSyncEnabled = bool

    @property
    def tempo(self):
        """Get the tempo of the clock"""
        return self._tempo
    
    @tempo.setter
    def tempo(self, value: int | float):
        """Set the tempo of the clock"""
        if self._link:
            # TODO: get a wrapper for these operations
            session = self._link.captureSessionState()
            session.setTempo(value, self._link.clock().micros())
            self._link.commitSessionState(session)

    @property
    def bar(self):
        """Get the bar of the clock"""
        return self._bar

    @property
    def beat(self):
        """Get the beat of the clock"""
        return self._beat

    @property
    def phase(self):
        """Get the phase of the clock"""
        return self._phase

    def start(self):
        """Start the clock"""
        if not self._clock_thread:
            self._clock_thread = threading.Thread(target=self.run).start()

    def play(self):
        """Play the clock"""
        session = self._link.captureSessionState()
        session.setIsPlaying(True, self._link.clock().micros())
        self._link.commitSessionState(session)

    def pause(self):
        """Pause the clock"""
        session = self._link.captureSessionState()
        session.setIsPlaying(False, self._link.clock().micros())
        self._link.commitSessionState(session)

    def stop(self):
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

    def run(self):
        """Clock Event Loop."""
        while not self._stop_event.is_set():
            self._capture_link_info()
            self._execute_due_events()
            sleep(0.001)


    def _execute_due_events(self):
        """Execute all due events."""
        while not self._event_queue.empty():
            event = self._event_queue.queue[0]
            if event.priority <= self._beat:
                self._event_queue.get()
                event.item()
                self._scheduled_events.remove(event)
            else:
                break

    def add(self, beat: int|float, func: Callable):
        """Add an event to the clock."""
        event = PriorityEvent(priority=beat, item=func)
        self._event_queue.put(event)
        self._scheduled_events.append(event)

    def remove(self, func: Callable):
        """Remove an event from the clock."""
        temp_queue = PriorityQueue(maxsize=1000)
        while not self._event_queue.empty():
            current_event = self._event_queue.get()
            if current_event.item != func:
                temp_queue.put(current_event)
            else:
                self._scheduled_events.remove(current_event)
        self._event_queue = temp_queue

