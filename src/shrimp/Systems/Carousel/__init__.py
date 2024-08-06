from .Pattern import *
from .Control import *
from .Base.BaseStream import *
from .Streams.CarouselStream import *
from ...environment import get_global_environment
from ...IO.osc import OSC
from .CarouselManager import CarouselPatternManager
from typing import Optional

env = get_global_environment()

carousel_osc = OSC(name="carousel", host="127.0.0.1", port=57120, clock=env.clock)
env.subscribe(carousel_osc)

CarouselManager = CarouselPatternManager()

RATE = 1 / 20
FRAME = RATE * 1e6


def vortex_clock_callback(start, ticks: int, session: "LinkSession", now: int | float) -> int:  # type: ignore
    """Emulation of the scheduler used by TidalVortex using a recursive function"""
    frame = (1 / 20) * 1e6
    logical_now, logical_next = (
        math.floor(start + (ticks * frame)),
        math.floor(start + ((ticks + 1) * frame)),
    )
    cycle_from, cycle_to = (
        session.beatAtTime(logical_now, 0) / env.clock._denominator,
        session.beatAtTime(logical_next, 0) / env.clock._denominator,
    )
    try:
        for player in CarouselManager._players.values():
            player.notify_tick(
                current_cycle=(cycle_from, cycle_to),
                link_session=session,
                cycles_per_second=env.clock.cps,
                beats_per_cycle=env.clock._denominator,
                now=now,
            )
    except Exception as _:
        print(_)

    return (logical_now - now) / 1e6


P = CarouselManager
