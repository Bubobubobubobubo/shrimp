from osc4py3 import oscbuildparse
from osc4py3.as_eventloop import *
from osc4py3.oscmethod import *
from ..environment import Subscriber
from typing import Optional
import threading
import time

class OSC(Subscriber):

    """OSC client: Send Open Sound Control messages to a remote host."""

    def __init__(self, name: str, host: str, port: int):
        super().__init__()
        self.name, self.host, self.port = name, host, port
        self.client = osc_udp_client(address=self.host, port=self.port, name=self.name)
        self._osc_loop_shutdown = threading.Event()
        self._osc_loop_thread: Optional[threading.Thread] = None
        self._nudge = 0.0

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