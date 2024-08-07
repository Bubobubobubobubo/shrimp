from .Utils import xorwise, identity
from .Pattern import fastcat
import math
from typing import TYPE_CHECKING, Optional, Callable
from itertools import accumulate
from .Pattern import Pattern, reify
from .TimeSpan import TimeSpan
from .Hap import Hap

from pyautogui import position as mouse_position
from pyautogui import size as screen_size


def saw() -> Pattern:
    """Returns a pattern that generates a saw wave between 0 and 1"""
    return signal(lambda t: t % 1)


def saw2() -> Pattern:
    """Returns a pattern that generates a saw wave between -1 and 1"""
    return saw().to_bipolar()


def isaw() -> Pattern:
    """Returns a pattern that generates an inverted saw wave between 0 and 1"""
    return signal(lambda t: 1 - (t % 1))


def isaw2() -> Pattern:
    """Returns a pattern that generates an inverted saw wave between -1 and 1"""
    return isaw().to_bipolar()


def tri() -> Pattern:
    """Returns a pattern that generates a triangle wave between 0 and 1"""
    return fastcat(isaw(), saw())


def tri2() -> Pattern:
    """Returns a pattern that generates a triangle wave between -1 and 1"""
    return fastcat(isaw2(), saw2())


def square() -> Pattern:
    """Returns a pattern that generates a square wave between 0 and 1"""
    return signal(lambda t: math.floor((t * 2) % 2))


def square2() -> Pattern:
    """Returns a pattern that generates a square wave between -1 and 1"""
    return square().to_bipolar()


def envL() -> Pattern:
    """
    Returns a Pattern of continuous Double values, representing
    a linear interpolation between 0 and 1 during the first cycle,
    then staying constant at 1 for all following cycles.
    """
    return signal(lambda t: max(0, min(t, 1)))


def envLR() -> Pattern:
    """
    Like envL but reversed.
    """
    return signal(lambda t: 1 - max(0, min(t, 1)))


def envEq() -> Pattern:
    """
    'Equal power' version of env, for gain-based transitions.
    """
    return signal(lambda t: math.sqrt(math.sin(math.pi / 2 * max(0, min(1 - t, 1)))))


def envEqR() -> Pattern:
    """
    Equal power reversed.
    """
    return signal(lambda t: math.sqrt(math.cos(math.pi / 2 * max(0, min(1 - t, 1)))))


def rand() -> Pattern:
    """
    Generate a continuous pattern of pseudo-random numbers between `0` and `1`.

    >>> rand().segment(4)

    """
    return signal(time_to_rand)


def irand(n: int) -> Pattern:
    """
    Generate a pattern of pseudo-random whole numbers between `0` to `n-1` inclusive.

    e.g this generates a pattern of 8 events per cycle, with values ranging from
    0 to 15 inclusive.

    >>> irand(16).segment(8)

    """
    return signal(lambda t: math.floor(time_to_rand(t) * n))


def _perlin_with(p: Pattern) -> Pattern:
    """
    1D Perlin noise. Takes a pattern as the RNG's "input" for Perlin noise, instead of
    automatically using the cycle count.

    """
    pa = p.with_value(math.floor)
    pb = p.with_value(lambda v: math.floor(v) + 1)

    def smoother_step(x: int | float) -> float:
        return 6.0 * x**5 - 15.0 * x**4 + 10.0 * x**3

    interp = lambda x: lambda a: lambda b: a + smoother_step(x) * (b - a)

    return (
        (p - pa)
        .with_value(interp)
        ._app_both(pa.with_value(time_to_rand))
        ._app_both(pb.with_value(time_to_rand))
    )


def perlin(p: Optional[Pattern] = None) -> Pattern:
    """
    1D Perlin (smooth) noise, works like rand but smoothly moves between random
    values each cycle.

    """
    if not p:
        p = signal(identity)
    return _perlin_with(p)


# Randomness
RANDOM_CONSTANT = 2**29
RANDOM_CYCLES_LENGTH = 300


def time_to_int_seed(a: float) -> int:
    """
    Stretch RANDOM_CYCLES_LENGTH cycles over the range of [0, RANDOM_CONSTANT]
    then apply the xorshift algorithm.

    """
    return xorwise(math.trunc((a / RANDOM_CYCLES_LENGTH) * RANDOM_CONSTANT))


def int_seed_to_rand(a: int) -> float:
    """Converts an integer seed to a random float between 0 and 1"""
    return (a % RANDOM_CONSTANT) / RANDOM_CONSTANT


def time_to_rand(a: float) -> float:
    """Converts a time value to a random float between 0 and 1"""
    return int_seed_to_rand(time_to_int_seed(a))


def signal(func: Callable) -> Pattern:
    """
    Base definition of a signal pattern. Returns an event with no whole, only a span and a value.
    The value is taken from the function applied to the midpoint of the span.
    """

    def _query(span: TimeSpan):
        return [Hap(None, span, func(span.midpoint()))]

    return Pattern(_query)


def sine() -> Pattern:
    """Returns a pattern that generates a sine wave between 0 and 1"""
    return signal(lambda t: (math.sin(math.pi * 2 * t) + 1) / 2)


def sine2() -> Pattern:
    """Returns a pattern that generates a sine wave between -1 and 1"""
    return signal(lambda t: math.sin(math.pi * 2 * t))


def cosine() -> Pattern:
    """Returns a pattern that generates a cosine wave between 0 and 1"""
    return sine().early(0.25)


def cosine2() -> Pattern:
    """Returns a pattern that generates a cosine wave between -1 and 1"""
    return sine2().early(0.25)


def mouseX() -> Pattern:
    """Returns a pattern that generates the x position of the mouse"""
    return signal(lambda _: mouse_position()[0] / screen_size()[0])


mousex = mouseX


def mouseY() -> Pattern:
    """Returns a pattern that generates the y position of the mouse"""
    return signal(lambda _: mouse_position()[1] / screen_size()[1])


mousey = mouseY


def wchoose(*vals):
    """Like @choose@, but works on an a list of tuples of values and weights"""
    return wchoose_with(rand(), *vals)


def wchoose_with(pat, *pairs):
    """
    Like `wchoose`, but works on an a list of tuples of values and weights

    Values are samples using the 0..1 ranged numerical pattern `pat`.

    """
    values, weights = list(zip(*pairs))
    cweights = list(accumulate(w for _, w in pairs))
    total = sum(weights)

    def match(r):
        if r < 0 or r > 1:
            raise ValueError("value from random pattern used by `wchooseby` is outside 0-1 range")
        indices = [i for i, c in enumerate(cweights) if c >= r * total]
        return values[indices[0]]

    return pat.with_value(match)


def choose(*vals):
    """Chooses randomly from the given list of values."""
    return choose_with(rand(), *vals)


def _choose_with(pat, *vals):
    return pat.range(0, len(vals)).with_value(lambda v: reify(vals[math.floor(v)]))


def choose_with(pat, *vals):
    """
    Choose from the list of values (or patterns of values) using the given
    pattern of numbers, which should be in the range of 0..1

    """
    return _choose_with(pat, *vals).outer_join()


def choose_cycles(*vals):
    """
    Similar to `cat`, but rather than playing the given patterns in order, it
    picks them at random.

    >>> s(choose_cycles("bd*2 sn", "jvbass*3", "drum*2", "ht mt")

    """
    return choose(*vals).segment(1)


def randcat(*vals):
    """Alias of `choose_cycles`"""
    return choose_cycles(*vals)
