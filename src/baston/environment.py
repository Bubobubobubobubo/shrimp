class Environment:
    def __init__(self):
        self.subscribers = []

    def subscribe(self, subscriber):
        self.subscribers.append(subscriber)
        subscriber.env = self

    def dispatch(self, sender, message_type: str, data: dict):
        for subscriber in self.subscribers:
            if subscriber != sender and message_type in subscriber.message_handlers:
                subscriber.message_handlers[message_type](data)

class Subscriber:
    def __init__(self):
        self.message_handlers = {}

    def register_handler(self, message_type: str, callback):
        self.message_handlers[message_type] = callback

