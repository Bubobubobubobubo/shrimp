from abc import ABC
from ..TimeSpan import TimeSpan
from ..Pattern import Pattern
from typing import Dict, Any, Optional
from ....IO.osc import OSC
from ....Time.Clock import Clock
from ....environment import Subscriber
import time


class BaseCarouselStream(ABC, Subscriber):
    """
    A class for playing control pattern events. It should be subscribed to a scheduler.

    Parameters
    ----------
    name: Optional[str]
        Name of the stream instance
    """

    def __init__(self, name: str = None, clock: Optional[Clock] = None):
        super().__init__()
        self.name = name
        self.pattern: Pattern = None
        self._clock = clock
        self._latency = 0.2

    def notify_tick(
        self,
        current_cycle: int,
        link_session: "LinkSession",  # type: ignore
        cycles_per_second: int | float,
        beats_per_cycle: int,
        now: int,
    ):
        """Called by a Clock every time it ticks, when subscribed to it"""
        if not self.pattern:
            return
        mill = 1e6
        unix_now = time.time()

        for event in self.pattern.onsets_only().query(TimeSpan(*current_cycle)):
            link_on, link_off = (
                link_session.timeAtBeat(event.whole.begin * beats_per_cycle, 0),
                link_session.timeAtBeat(event.whole.end * beats_per_cycle, 0),
            )
            delta_secs = (link_off - link_on) / mill

            # # Calculate timestamp
            # link_secs = now / mill
            # link_to_unix_offset = unix_now - link_secs
            # ts = (
            #     (link_on / mill) + link_to_unix_offset + self._latency + event.value.get("nudge", 0)
            # )
            ts = time.time()

            self.notify_event(
                event.value,
                timestamp=ts,
                cps=float(cycles_per_second),
                cycle=float(event.whole.begin),
                delta=float(delta_secs),
            )

    def notify_event(
        self,
        event: Dict[str, Any],
        timestamp: float,
        cps: float,
        cycle: float,
        delta: float,
    ):
        """Called by `notify_tick` with the event and timestamp that should be played"""
        raise NotImplementedError

    def __repr__(self):
        pattern_repr = " \n" + repr(self.pattern) if self.pattern else ""
        return f"<{self.__class__.__name__} {repr(self.name)}{pattern_repr}>"
