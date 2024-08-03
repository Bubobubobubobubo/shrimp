from .Pattern import *
from .Control import *
from .Base.BaseStream import *
from .Streams.CarouselStream import *
from ...environment import get_global_environment
from ...io.osc import OSC
import logging
from typing import Optional

env = get_global_environment()
carousel_osc = OSC(name="carousel", host="127.0.0.1", port=57120, clock=env.clock)
env.subscribe(carousel_osc)


class CarouselPatternManager:
    """Pattern manager for Carousel"""

    def __init__(self, clock: Optional[Clock] = None):
        self._players: Dict[str, CarouselStream] = {}
        self._clock = clock

    def __setattr__(self, name: str, value):
        if isinstance(value, Pattern):
            if name not in self._players:
                self._players[name] = CarouselStream(clock=env.clock, name=name)
                env.subscribe(self._players[name])
            self._players[name].pattern = value
        else:
            super().__setattr__(name, value)

    def __getattr__(self, name: str) -> CarouselStream:
        if name not in self._players:
            self._players[name] = CarouselStream(clock=env.clock, name=name)
            env.subscribe(self._players[name])
        return self._players[name]

    def clear(self):
        """Clear all players"""
        self._players.clear()

    def __iter__(self):
        return iter(self._players.values())

    def get_player(self, name: str) -> Optional[CarouselStream]:
        return self._players.get(name)

    def remove_player(self, name: str):
        if name in self._players:
            del self._players[name]

    def list_players(self):
        return list(self._players.keys())

    def update_player(self, name: str, pattern: Pattern):
        if name in self._players:
            self._players[name].pattern = pattern
        else:
            new_stream = CarouselStream(clock=env.clock, name=name)
            new_stream.pattern = pattern
            self._players[name] = new_stream

    def __repr__(self):
        return f"CarouselPatternManager(players={list(self._players.keys())})"


CarouselManager = CarouselPatternManager()


def vortex_clock(ticks=0, start=0):
    """Emulation of the scheduler used by TidalVortex using a recursive function"""
    if ticks == 0:
        start = env.clock._link.clock().micros()
    rate = 1 / 20
    frame = rate * 1e6
    session = env.clock._link.captureAppSessionState()
    now = env.clock._link.clock().micros()

    logical_now, logical_next = (
        math.floor(start + (ticks * frame)),
        math.floor(start + ((ticks + 1) * frame)),
    )

    try:
        for player in CarouselManager._players.values():
            player.notify_tick(
                current_cycle=(env.clock.beat, env.clock.beat + rate),
                link_session=session,
                cycles_per_second=env.clock.cps,
                beats_per_cycle=env.clock._denominator,
                now=now,
            )
    except Exception as _:
        print(_)

    timeref = env.clock._events.get("vortex_clock", None)
    timeref = timeref.next_time if timeref is not None else env.clock.next_bar

    env.clock.add(
        name="vortex_clock",
        func=vortex_clock,
        time_reference=timeref,
        time=rate,
        ticks=ticks + 1,
        start=start,
    )


P = CarouselManager

env.clock.add(
    name="clock_start", func=lambda: vortex_clock(), time_reference=env.clock.next_bar, time=0
)
