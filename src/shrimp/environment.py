from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .time.clock import Clock


class Environment:
    def __init__(self):
        self._subscribers = []
        self._clock: Optional["Clock"] = None

    @property
    def clock(self):
        if self._clock is None:
            pass
        else:
            return self._clock

    def add_clock(self, clock: "Clock"):
        if self._clock is not None:
            pass
        else:
            self._clock = clock
            self.subscribe(self._clock)

    @property
    def subscribers(self):
        return self._subscribers

    def subscribe(self, subscriber):
        self._subscribers.append(subscriber)
        subscriber.env = self

    def dispatch(self, sender, message_type: str, data: dict):
        for subscriber in self._subscribers:
            if subscriber != sender and message_type in subscriber.message_handlers:
                subscriber.message_handlers[message_type](data)


class Subscriber:
    def __init__(self):
        self.message_handlers = {}

    def register_handler(self, message_type: str, callback):
        self.message_handlers[message_type] = callback


environment = Environment()


def get_global_environment():
    return environment
