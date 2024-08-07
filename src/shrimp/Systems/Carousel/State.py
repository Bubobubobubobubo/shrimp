from .TimeSpan import TimeSpan
from typing import Callable

class State:
    def __init__(self, span: TimeSpan, controls: dict):
        self.span = span
        self.controls = controls

    def set_span(self, span: TimeSpan):
        self.span = span
    
    def with_span(self, func: Callable):
        return self.set_span(func(self.span))

    def set_controls(self, controls: dict):
        return State(self.span, controls)