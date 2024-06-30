from osc4py3 import oscbuildparse
from osc4py3.as_eventloop import *
from osc4py3.oscmethod import *
from ..environment import Subscriber
from ..utils import flatten, kwargs_to_flat_list
from typing import Optional, Any, Callable
import threading
import time

class OSC(Subscriber):

    """OSC client: Send/Receive Open Sound Control messages to/from a remote host."""

    def __init__(self, name: str, host: str, port: int):
        super().__init__()
        self.name, self.host, self.port = name, host, port
        self.client = osc_udp_client(address=self.host, port=self.port, name=self.name)
        self._osc_loop_shutdown = threading.Event()
        self._osc_loop_thread: Optional[threading.Thread] = None
        self._nudge = 0.0

        # OSC-In communication
        self._watched_values = {}

        # Initialise the background OSC process loop
        self.setup_osc_loop()

        # Event handlers
        self.register_handler("stop", lambda: self._osc_loop_shutdown.set())

    def setup_osc_loop(self) -> None:
        """Initialise the background OSC process loop."""

        def _osc_process_loop():
            """Background OSC processing loop.

            Note: This function is intended to be run in a separate thread.
            It should call osc_process() repeatedly to keep the OSC server 
            alive. It will run until the _osc_loop_shutdown event is set.
            """
            while not self._osc_loop_shutdown.is_set():
                osc_process()
                time.sleep(0.1)

        osc_startup()
        self._osc_loop_thread = threading.Thread(target=_osc_process_loop, daemon=True)
        self._osc_loop_thread.start()

    @property
    def nudge(self):
        """Nudge time in seconds."""
        return self._nudge

    @nudge.setter
    def nudge(self, value: float):
        """Set the nudge time in seconds."""
        self._nudge = value

    def __repr__(self):
        return f"<OSC {self.host}:{self.port}>"

    def __str__(self):
        return self.__repr__()

    def _send(self, address: str, message: list) -> None:
        """Send an OSC message to the client.
        
        Args:
            address (str): The OSC address.
            message (list): The OSC message.
        """
        bundle = self._make_bundle([[address, message]])
        osc_send(bundle, self.name)

    def _dirt_play(self, *args, **kwargs) -> None:
        """Send a /dirt/play message to the SuperDirt audio engine.
        
        Args:
            *args: all discarded!
            **kwargs: Arbitrary keyword arguments.

        Note: This method is intended to be used as a helper function to send
        messages to the SuperDirt audio engine. The kwargs are converted to a
        flat list of key-value pairs.
        """
        self._send(address="/dirt/play", message=kwargs_to_flat_list(**kwargs))

    def panic(self) -> None:
        """Send a panic message to the SuperDirt audio engine."""
        self._dirt_play(sound="superpanic")

    def _make_bundle(self, messages: list) -> oscbuildparse.OSCBundle:
        """Create an OSC bundle.

        Args:
            messages (list): A list of OSC messages.
        """
        return oscbuildparse.OSCBundle(
            oscbuildparse.unixtime2timetag(time.time() + self._nudge),
            [
                oscbuildparse.OSCMessage(message[0], None, message[1])
                for message in messages
            ],
        )

    def _send_bundle(self, messages: list) -> None:
        """Send an OSC bundle to the client.

        Args:
            messages (list): A list of OSC messages.

        """
        bundle = self._make_bundle(messages)
        osc_send(bundle, self.name)

    def _generic_store(self, address) -> None:
        """Generic storage function to attach to a given address

        Args:
            address (str): The OSC address to store the value of.
        """

        def generic_value_tracker(*args, **kwargs):
            """Generic value tracker to be attached to an address"""
            self._watched_values[address] = {"args": flatten(args), "kwargs": kwargs}
            return (args, kwargs)

        osc_method(address, generic_value_tracker, argscheme=OSCARG_DATA)

    def watch(self, address: str) -> None:
        """
        Watch the value of a given OSC address. Will be recorded in memory
        in the self._watched_values dictionary accessible through the get()
        method

        Args:
            address (str): The OSC address to watch.
        """
        print(f"[yellow]Watching address [red]{address}[/red].[/yellow]")
        self._generic_store(address)

    def attach(
        self, address: str, function: Callable, watch: bool = False, argscheme=None
    ) -> None:
        """
        Attach a callback to a given address. You can also toggle the watch boolean 
        value to tell if the value should be tracked by the receiver. This allows to
        return values from the callback that you can retrieve later on through 
        the get(address) method.

        Args:
            address (str): The OSC address to attach the function to.
            function (Callable): The function to attach.
            watch (bool): Whether to watch the value of the address.
            argscheme: The OSC argument scheme.

        """
        print(f"[yellow]Attaching function [red]{function.__name__}[/red] to address [red]{address}[/red][/yellow]")
        osc_method(
            address,
            function,
            argscheme=OSCARG_DATAUNPACK if argscheme is None else argscheme,
        )
        if watch:
            self.watch(address)

    def get(self, address: str) -> Any | None:
        """Get a watched value. Return None if not found"""
        try:
            return self._watched_values[address]
        except KeyError:
            return None