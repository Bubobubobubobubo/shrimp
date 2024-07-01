from importlib.metadata import version
from rich.panel import Panel
from rich import print
from pyfiglet import figlet_format
import random


def info_message(message: str, should_print: bool = False) -> None:
    """Print an information message"""
    if should_print:
        print(Panel(f"[bold blue]{message}[/bold blue]"))


def greeter() -> None:
    font_choice = random.choice(["roman", "basic", "computer"])
    banner = figlet_format("Baston", font=font_choice)
    print(
        f"[bold blue]{banner}[/bold blue][bold yellow]\n> Live Coding tool, BuboBubo {version('baston')}[/bold yellow]",
        end="",
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
