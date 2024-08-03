from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .Time.Clock import Clock


class Environment:
    """The Environment class is a global object that holds all the components of the system."""

    def __init__(self):
        self._subscribers = []
        self._clock: Optional["Clock"] = None

    @property
    def clock(self):
        """Return the global clock of the system"""
        if self._clock is None:
            pass
        else:
            return self._clock

    def add_clock(self, clock: "Clock"):
        """Add a global clock to the environment"""
        if self._clock is not None:
            pass
        else:
            self._clock = clock
            self.subscribe(self._clock)

    @property
    def subscribers(self):
        """Return the subscribers of the global environment"""
        return self._subscribers

    def subscribe(self, subscriber: "Subscriber") -> None:
        """Subscribe a component to the global environment
        Args:
            subscriber: The component to subscribe to the global environment

        """
        self._subscribers.append(subscriber)
        subscriber.env = self

    def dispatch(self, sender, message_type: str, data: dict) -> None:
        """
        Dispatch a message to all subscribers

        Args:
            sender: The sender of the message
            message_type: The type of message
            data: The data of the
        """
        for subscriber in self._subscribers:
            if subscriber != sender and message_type in subscriber.message_handlers:
                subscriber.message_handlers[message_type](data)


class Subscriber:
    """A class that can subscribe to the global environment"""

    def __init__(self):
        self.message_handlers = {}

    def register_handler(self, message_type: str, callback):
        """Register a message handler"""
        self.message_handlers[message_type] = callback


environment = Environment()


def get_global_environment():
    """Return the global environment"""
    return environment
