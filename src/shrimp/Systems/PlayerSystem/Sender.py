from dataclasses import dataclass
from typing import Any, Callable, Optional, TypeVar, ParamSpec

P = ParamSpec("P")
T = TypeVar("T")


@dataclass
class Sender:
    """
    PlayerPattern class to store the pattern information. Every pattern is a PlayerPattern object.
    """

    send_method: Callable[P, T]  # type: ignore
    args: tuple[Any]
    kwargs: dict[str, Any]
    manual_polyphony: bool = False
    iterations: int = 0
