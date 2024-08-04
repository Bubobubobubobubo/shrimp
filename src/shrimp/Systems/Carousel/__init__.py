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


def vortex_clock(ticks=0, start=0):
    """Emulation of the scheduler used by TidalVortex using a recursive function"""
    if ticks == 0:
        start = env.clock._link.clock().micros()
    rate = 1 / 20
    frame = rate * 1e6
    session = env.clock._link.captureSessionState()
    now = env.clock._link.clock().micros()

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
