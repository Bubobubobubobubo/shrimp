from importlib.metadata import version
from rich.panel import Panel
from rich import print
from typing import Callable, ParamSpec, TypeVar
from pyfiglet import figlet_format
import shutil
import random
import functools

P = ParamSpec("P")
T = TypeVar("T")

MISSING = object()


def alias_param(name: str, alias: str):
    """
    Alias a keyword parameter in a function. Throws a TypeError when a value is
    given for both the original kwarg and the alias. Method taken from
    github.com/thegamecracks/abattlemetrics/blob/main/abattlemetrics/client.py
    (@thegamecracks).
    """

    def deco(func: Callable[P, T]):
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            alias_value = kwargs.pop(alias, MISSING)
            if alias_value is not MISSING:
                if name in kwargs:
                    raise TypeError(f"Cannot pass both {name!r} and {alias!r} in call")
                kwargs[name] = alias_value
            return func(*args, **kwargs)

        return wrapper

    return deco


def info_message(message: str, should_print: bool = False) -> None:
    """Print an information message"""
    if should_print:
        print(Panel(f"[bold blue]{message}[/bold blue]"))


def greeter() -> None:
    font_choice = random.choice(["roman", "basic", "computer"])
    banner = figlet_format("Shrimp", font=font_choice)
    # Detect terminal size
    terminal_size = shutil.get_terminal_size()
    # Get length of one line of the banner string
    banner_length = len(banner.split("\n")[0])
    if banner_length > terminal_size.columns:
        banner = "=== BASTON ==="
    print(
        f"[bold blue]{banner}[/bold blue][bold yellow]\n> Live Coding tool, BuboBubo {version('shrimp')}[/bold yellow]",
    )


def flatten(l: list) -> list:
    """Utility function to flatten a list.

    Args:
        l (list): A list to flatten
    """
    if isinstance(l, (list, tuple)):
        if len(l) > 1:
            return [l[0]] + flatten(l[1:])
        else:
            return l[0]
    else:
        return [l]


def kwargs_to_flat_list(**kwargs):
    """
    Convert keyword arguments to a flat list of key-value pairs.

    Parameters:
        **kwargs: Arbitrary keyword arguments.

    Returns:
        List where each key is followed by its value.
    """
    flat_list = []
    for key, value in kwargs.items():
        flat_list.append(key)
        flat_list.append(value)
    return flat_list


def euclidian_rhythm(pulses: int, length: int, rotate: int = 0):
    """Calculate Euclidean rhythms."""

    def _starts_descent(list, index):
        length = len(list)
        next_index = (index + 1) % length
        return list[index] > list[next_index]

    if pulses >= length:
        return [1]
    res_list = [pulses * t % length for t in range(-1, length - 1)]
    bool_list = [_starts_descent(res_list, index) for index in range(length)]

    def rotation(l, n):
        return l[-n:] + l[:-n]

    return rotation([1 if x is True else 0 for x in bool_list], rotate)
