from typing import Dict, Optional
from .Streams.CarouselStream import CarouselStream
from ...Time.Clock import Clock
from .Pattern import Pattern
from ...environment import get_global_environment

env = get_global_environment()


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
        """Get a player by name"""
        return self._players.get(name)

    def remove_player(self, name: str):
        """Remove a player"""
        if name in self._players:
            del self._players[name]

    def list_players(self):
        """List all players"""
        return list(self._players.keys())

    def update_player(self, name: str, pattern: Pattern):
        """Update a player with a new pattern"""
        if name in self._players:
            self._players[name].pattern = pattern
        else:
            new_stream = CarouselStream(clock=env.clock, name=name)
            new_stream.pattern = pattern
            self._players[name] = new_stream

    def __repr__(self):
        return f"CarouselPatternManager(players={list(self._players.keys())})"
