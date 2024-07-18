import mido
from ..time.clock import Clock
from ..environment import Subscriber
import threading
from time import sleep
from typing import Dict, Optional
from ..utils import linear_scaling


class CCStorage:
    """A class to store control change messages for a given channel and control number"""

    def __init__(self):
        self._cc_messages: Dict[int, Dict[int, int]] = {}

    def add_message(self, channel: int, control_number: int, value: int) -> None:
        """Add a control change message to the storage.

        Args:
            channel (int): The MIDI channel.
            control_number (int): The control number.
            value (int): The control value.
        """
        if channel not in self._cc_messages:
            self._cc_messages[channel] = {}
        self._cc_messages[channel][control_number] = value

    def get_message(self, channel: int, control_number: int) -> Optional[int]:
        """Get a control change message from the storage.

        Args:
            channel (int): The MIDI channel.
            control_number (int): The control number.

        Returns:
            Optional[int]: The control value, or None if the message is not found.
        """
        return self._cc_messages.get(channel, {}).get(control_number, None)


def _clamp_midi(value: int) -> int:
    """Clamp a MIDI value to the range [0, 127]."""
    return max(0, min(127, value))


def list_midi_ports() -> list[str]:
    """List the available MIDI ports."""
    return mido.get_input_names()


class MIDIIn(Subscriber):
    """MIDI class to receive MIDI messages from a MIDI port."""

    def __init__(self, port: str, clock: Clock):
        super().__init__()
        self.port = port
        self.clock = clock
        self.wheel = 0
        self._midi_loop_thread = None
        self._midi_loop_shutdown = threading.Event()
        self._received_controls = CCStorage()

        try:
            if self.port == "shrimp":
                self._midi_in = mido.open_input(port, virtual=True)
            else:
                self._midi_in = mido.open_input(port)
        except:
            print(f"Could not open MIDI port {port}")

        # Initialise the background MIDI-In monitoring loop
        self._setup_midi_loop()

        # Registering handlers
        self.register_handler("stop", lambda _: self._midi_loop_shutdown.set())

    def _setup_midi_loop(self) -> None:
        """Setup the MIDI monitoring loop."""

        def _midi_process_loop():
            """Listen for MIDI messages and process them."""
            while not self._midi_loop_shutdown.is_set():
                for message in self._midi_in:
                    if message.type == "control_change":
                        self._received_controls.add_message(
                            channel=message.channel + 1,
                            control_number=message.control + 1,
                            value=message.value,
                        )
                sleep(0.01)

        self._midi_loop_thread = threading.Thread(target=_midi_process_loop, daemon=True)
        self._midi_loop_thread.start()

    def cc(self, channel: int, control: int, default_value: int = 60) -> int:
        """Get the value of a MIDI control change message.

        Args:
            control (int): The control number.
            channel (int): The MIDI channel.

        Returns:
            int: The value of the control.
        """
        value = self._received_controls.get_message(channel, control)
        if value is None:
            return default_value
        return value


class MIDIOut(Subscriber):
    """MIDI class to send MIDI messages to a MIDI port."""

    def __init__(self, port: str, clock: Clock):
        super().__init__()
        self.port = port
        self.clock = clock
        self.nudge = -0.1
        try:
            if self.port == "shrimp":
                self._midi_out = mido.open_output(port, virtual=True)
            else:
                self._midi_out = mido.open_output(port)
        except:
            print(f"Could not open MIDI port {port}")
        self.pressed_notes: Dict[int, Dict[int, bool]] = {
            i: {} for i in range(16)
        }  # Track pressed notes per channel

        self.register_handler("pause", self._pause_handler)
        self.register_handler("stop", self._stop_handler)
        self.register_handler("all_notes_off", lambda _: self.all_notes_off())

    def _pause_handler(self, data: dict) -> None:
        """Handle the pause event."""
        self.all_notes_off()

    def _stop_handler(self, data: dict) -> None:
        """Handle the stop event."""
        self.all_notes_off()

    def all_notes_off(self):
        """Send all notes off message on all channels."""
        for channel in range(16):
            for notes in range(128):
                self._note_off(note=notes, channel=channel)

    def _note_on(self, note: int = 60, velocity: int = 100, channel: int = 1) -> None:
        """Send a MIDI note on message:

        Args:
            note (int): The MIDI note number.
            velocity (int): The velocity of the note.
            channel (int): The MIDI channel.

        """
        # Send note_off if the note is already pressed
        if self.pressed_notes[channel].get(note, False):
            self._note_off(note=note, channel=channel, velocity=0)
        self.pressed_notes[channel][note] = True
        midi_message = mido.Message("note_on", note=note, velocity=velocity, channel=channel)
        self._midi_out.send(midi_message)

    def _note_off(self, note: int = 60, velocity: int = 0, channel: int = 1) -> None:
        """Send a MIDI note off message.

        Args:
            note (int): The MIDI note number.
            velocity (int): The velocity of the note.
            channel (int): The MIDI channel.
        """
        self.pressed_notes[channel][note] = False
        midi_message = mido.Message("note_off", note=note, velocity=velocity, channel=channel)
        self._midi_out.send(midi_message)

    def note(
        self,
        note: int | list[int] = 60,
        velocity: int = 0.75,
        channel: int = 1,
        length: int = 1,
        **kwargs,
    ):
        """Play a note for a given duration.

        Args:
            note (int): The MIDI note number.
            velocity (int): The velocity of the note.
            channel (int): The MIDI channel.
            duration (int): The duration of the note in beats.

        Note: This function schedules the note on and note off messages to be sent
        at the appropriate times using the clock.
        """
        note = (
            _clamp_midi(int(note)) if isinstance(note, int) else [_clamp_midi(int(n)) for n in note]
        )
        velocity = _clamp_midi(int(linear_scaling(velocity, 0.0, 1.0, 0, 127)))
        length = length * self.clock.beat_duration
        time = self.clock.now - self.nudge

        if isinstance(note, list):
            for n in note:
                self.note(note=int(n), velocity=velocity, channel=channel, length=length)
            return

        self.clock.add(
            func=lambda: self._note_on(
                note=int(note), velocity=int(velocity), channel=int(channel) - 1
            ),
            time=time,
            once=True,
        )
        self.clock.add(
            func=lambda: self._note_off(note=int(note), velocity=0, channel=int(channel) - 1),
            time=(time + length) - 0.020,
            once=True,
        )

    def tick(self, *args, **kwargs):
        """Send a MIDI clock message."""
        self._midi_out.send(mido.Message("clock"))

    def start(self, *args, **kwargs):
        """Send a MIDI start message."""
        self._midi_out.send(mido.Message("start"))

    def stop(self, *args, **kwargs):
        """Send a MIDI stop message."""
        self._midi_out.send(mido.Message("stop"))

    def pitch_bend(self, value: int = 0, channel: int = 1, **kwargs) -> None:
        """Send a MIDI pitch bend message.

        Args:
            value (int): The pitch bend value.
            channel (int): The MIDI channel.
        """
        pb = mido.Message("pitchwheel", pitch=value, channel=channel)
        self._midi_out.send(pb)

    def control_change(self, control: int = 0, value: int = 0, channel: int = 1, **kwargs) -> None:
        """Send a MIDI control change message.

        Args:
            control (int): The control number.
            value (int): The control value.
            channel (int): The MIDI channel.
        """
        cc = mido.Message("control_change", control=control, value=value, channel=channel)
        self._midi_out.send(cc)

    def program_change(self, program: int = 0, channel: int = 1, **kwargs) -> None:
        """Send a MIDI program change message.

        Args:
            program (int): The program number.
            channel (int): The MIDI channel.
        """
        pc = mido.Message("program_change", program=program, channel=channel)
        self._midi_out.send(pc)

    def sysex(self, data: list, *kwargs) -> None:
        """Send a MIDI system exclusive message.

        Args:
            data (list): The sysex data.
        """
        sysex = mido.Message("sysex", data=data)
        self._midi_out.send(sysex)

    def make_instrument(self, channel: int, control_map: dict[str, int]):
        """
        Create a function to control a MIDI instrument.

        Args:
            channel (int): The MIDI channel.
            control_map (dict[str, int]): A mapping of control names to control numbers.

        Returns:
            function: A function to control the MIDI instrument.
        """

        def instrument_controller(*args, **kwargs):
            # Handle note messages
            if "note" in kwargs:
                note = kwargs["note"]
                velocity = kwargs.get("velocity", 100)
                duration = kwargs.get("duration", 1)
                self.note(note=note, velocity=velocity, channel=channel, duration=duration)

            # Handle control change messages
            for control_name, control_value in kwargs.items():
                if control_name in control_map:
                    control_number = control_map[control_name]
                    self.control_change(
                        control=control_number, value=control_value, channel=channel
                    )

            # Handle program change message
            if "program_change" in kwargs:
                program = kwargs["program_change"]
                self.program_change(program=program, channel=channel)

        return instrument_controller

    def make_controller(self, channel: int, control_map: dict[str, int]):
        """
        Create a function to control MIDI hardware/software.

        Args:
            channel (int): The MIDI channel.
            control_map (dict[str, int]): A mapping of control names to control numbers.

        Returns:
            function: A function to control the MIDI instrument.
        """

        def controller_interface(*_, **kwargs):
            # Handle control change messages
            for control_name, control_value in kwargs.items():
                if control_name in control_map:
                    control_number = control_map[control_name]
                    self.control_change(
                        control=control_number, value=control_value, channel=channel
                    )

            # Handle program change message
            if "program_change" in kwargs:
                program = kwargs["program_change"]
                self.program_change(program=program, channel=channel)

        return controller_interface
