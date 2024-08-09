from osc4py3 import oscbuildparse
from osc4py3.oscbuildparse import OSCtimetag
from osc4py3.as_eventloop import *
from osc4py3.oscmethod import *
from ..environment import Subscriber
from ..Time.Clock import Clock
from ..utils import flatten, kwargs_to_flat_list
from typing import Optional, Any, Callable, Optional
from ..Systems.PlayerSystem.Rest import Rest
import threading
import logging
import time


class OSC(Subscriber):
    """OSC client: Send/Receive Open Sound Control messages to/from a remote host."""

    def __init__(self, name: str, host: str, port: int, clock: Clock):
        super().__init__()
        self.name, self.host, self.port = name, host, port
        self._clock = clock
        self.client = osc_udp_client(address=self.host, port=self.port, name=self.name)
        self._osc_loop_shutdown = threading.Event()
        self._osc_loop_thread: Optional[threading.Thread] = None
        self._nudge = 0.1

        # OSC-In communication
        self._watched_values = {}

        # Initialise the background OSC process loop
        self.setup_osc_loop()

        # Event handlers
        self.register_handler("stop", lambda _: self._stop(_))
        self.register_handler("silence", lambda _: self.panic())

    def _stop(self, _):
        """Stops the OSC processing loop"""
        self._osc_loop_shutdown.set()
        self._osc_loop_thread.join()

    def setup_osc_loop(self) -> None:
        """Initialise the background OSC process loop."""

        def _osc_process_loop():
            """Background OSC processing loop.

            Note: This function is intended to be run in a separate thread.
            It should call osc_process() repeatedly to keep the OSC server
            alive. It will run until the _osc_loop_shutdown event is set.
            """
            try:
                while not self._osc_loop_shutdown.is_set():
                    osc_process()
                    time.sleep(0.001)
            except BlockingIOError:
                pass

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

    def send(self, address: str, messages: list, timestamp: Optional[float] = None) -> None:
        """Send one or multiple timestamped OSC messages to the client. The expected format
           for the timestamp is a Unix timetag (float). Conversion into OSC Timetag is done
           by this method.

        Args:
            address (str): The OSC address.
            messages (list): A list of messages to send.
            timestamp (Optional[float]): The Unix timestamp of the message.
        """
        messages = [
            oscbuildparse.OSCMessage(
                addrpattern=address, typetags=None, arguments=message  # auto-detect types
            )
            for message in messages
        ]

        bundle = oscbuildparse.OSCBundle(
            timetag=(
                oscbuildparse.unixtime2timetag(timestamp)
                if timestamp
                else oscbuildparse.OSC_IMMEDIATELY
            ),
            elements=messages,
        )
        try:
            osc_send(bundle, self.name)
        except Exception as e:
            logging.error(f"Error sending OSC messages: {e}")

    def dirt(self, **kwargs) -> None:
        """Send a /dirt/play message to the SuperDirt audio engine.

        Args:
            *args: all discarded!
            **kwargs: Arbitrary keyword arguments.

        Note: This method is intended to be used as a helper function to send
        messages to the SuperDirt audio engine. The kwargs are converted to a
        flat list of key-value pairs.
        """
        kwargs.update(
            {
                "cps": (self._clock.tempo / self._clock._denominator) / 60,
                "cycle": self._clock.beat,
                "delta": self._clock.beat,
            }
        )
        self._send_timed_message(address="/dirt/play", message=kwargs_to_flat_list(**kwargs))

    def player_dirt(self, *args, **kwargs):
        """Alternative version for the systems/Player pattern system."""
        sound = kwargs.pop("sound", None)
        n = kwargs.pop("n", None)

        if isinstance(sound, list) and sound:
            max_length = max(
                len(sound), *(len(v) if isinstance(v, list) else 1 for v in kwargs.values())
            )
        else:
            max_length = max((len(v) if isinstance(v, list) else 1) for v in kwargs.values())

        if isinstance(n, list) and n:
            max_length = max(max_length, len(n))

        # Prepare arguments for each iteration
        for i in range(max_length):
            iter_kwargs = {}
            for k, v in kwargs.items():
                if isinstance(v, list):
                    iter_kwargs[k] = v[i % len(v)]  # Cycle through the list if needed
                else:
                    iter_kwargs[k] = v

            iter_sound = sound[i % len(sound)] if isinstance(sound, list) and sound else sound
            iter_n = n[i % len(n)] if isinstance(n, list) and n else n

            if iter_sound is not None and iter_n is not None:
                iter_kwargs["sound"] = f"{iter_sound}:{iter_n}"
            elif iter_sound is not None:
                iter_kwargs["sound"] = iter_sound
            elif iter_n is not None:
                iter_kwargs["sound"] = iter_n

            iter_kwargs = kwargs_to_flat_list(**iter_kwargs)
            iter_kwargs = [
                value.to_number() if isinstance(value, Rest) else value for value in iter_kwargs
            ]
            self._send_timed_message(address="/dirt/play", message=iter_kwargs)

    def player_dirt(self, *args, **kwargs):
        """Alternative version for the systems/Player pattern system."""
        sound = kwargs.pop("sound", None)
        n = kwargs.pop("n", None)

        # Determine max length based on sound, n, and other kwargs
        max_length = 1

        if isinstance(sound, list) and sound:
            max_length = max(max_length, len(sound))
        if isinstance(n, list) and n:
            max_length = max(max_length, len(n))
        for v in kwargs.values():
            if isinstance(v, list):
                max_length = max(max_length, len(v))

        # Prepare arguments for each iteration
        for i in range(max_length):
            iter_kwargs = {}
            for k, v in kwargs.items():
                if isinstance(v, list):
                    iter_kwargs[k] = v[i % len(v)]  # Cycle through the list if needed
                else:
                    iter_kwargs[k] = v

            iter_sound = sound[i % len(sound)] if isinstance(sound, list) and sound else sound
            iter_n = n[i % len(n)] if isinstance(n, list) and n else n

            if iter_sound is not None and iter_n is not None:
                iter_kwargs["sound"] = f"{iter_sound}:{iter_n}"
            elif iter_sound is not None:
                iter_kwargs["sound"] = iter_sound
            elif iter_n is not None:
                iter_kwargs["sound"] = iter_n

            iter_kwargs = kwargs_to_flat_list(**iter_kwargs)
            iter_kwargs = [
                value.to_number() if isinstance(value, Rest) else value for value in iter_kwargs
            ]
            self._send_timed_message(address="/dirt/play", message=iter_kwargs)

    def panic(self, _={}) -> None:
        """Send a panic message to the SuperDirt audio engine."""
        self.dirt(sound="superpanic")

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

    def attach(self, address: str, function: Callable, watch: bool = False, argscheme=None) -> None:
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
        print(
            f"[yellow]Attaching function [red]{function.__name__}[/red] to address [red]{address}[/red][/yellow]"
        )
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
