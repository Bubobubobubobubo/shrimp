import mido
from ..time.clock import Clock
from ..environment import Subscriber

def list_midi_ports() -> list[str]:
    """List the available MIDI ports."""
    return mido.get_input_names()


class MIDIIn(Subscriber):
    """MIDI class to receive MIDI messages from a MIDI port."""

    # TODO: continue implementation

    def __init__(self, port: str, clock: Clock):
        super().__init__()
        self.port = port
        self.clock = clock
        self.wheel = 0
        try:
            self._midi_in = mido.open_input(port)
        except:
            print(f"Could not open MIDI port {port}")

    def _monitoring_loop(self):
        """Monitor the MIDI port for incoming messages."""
        for message in self._midi_in:
            if message.type == "pitchwheel":
                self.wheel = message.pitch
            if message.type == "stop":
                self.clock.stop()
            if message.type in ["start", "continue"]:
                self.clock.play()

        self.clock.add(self.clock.beat + 0.01, self._monitoring_loop)


class MIDIOut(Subscriber):
    """MIDI class to send MIDI messages to a MIDI port."""

    def __init__(self, port: str, clock: Clock):
        super().__init__()
        self.port = port
        self.clock = clock
        try:
            self._midi_out = mido.open_output(port)
        except:
            print(f"Could not open MIDI port {port}")

        self.register_handler("pause", self._pause_handler)
        self.register_handler("stop", self._stop_handler)
        self.register_handler("all_notes_off", lambda _: self._all_notes_off())

    def _pause_handler(self, data: dict) -> None:
        """Handle the pause event."""
        self._all_notes_off()

    def _stop_handler(self, data: dict) -> None:
        """Handle the stop event."""
        self._all_notes_off()

    def _all_notes_off(self):
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
        note = mido.Message("note_on", note=note, velocity=velocity, channel=channel)
        self._midi_out.send(note)

    def _note_off(self, note: int = 60, velocity: int = 0, channel: int = 1) -> None:
        """Send a MIDI note off message.

        Args:
            note (int): The MIDI note number.
            velocity (int): The velocity of the note.
            channel (int): The MIDI channel.
        """
        note = mido.Message("note_off", note=note, velocity=velocity, channel=channel)
        self._midi_out.send(note)

    def note(self, note: int = 60, velocity: int = 100, channel: int = 1, duration: int = 1):
        """Play a note for a given duration.

        Args:
            note (int): The MIDI note number.
            velocity (int): The velocity of the note.
            channel (int): The MIDI channel.
            duration (int): The duration of the note in beats.

        Note: This function schedules the note on and note off messages to be sent
        at the appropriate times using the clock.
        """
        epsilon = duration / 100
        self.clock.add(
            func=lambda: self._note_on(note, velocity, channel - 1), time=self.clock.beat, once=True
        )
        self.clock.add(
            func=lambda: self._note_off(note, 0, channel - 1),
            time=self.clock.beat + (duration - epsilon),
            once=True,
        )

    def cc(self, control: int = 0, value: int = 0, channel: int = 1) -> None:
        """Send a MIDI control change message.

        Args:
            control (int): The control number.
            value (int): The control value.
            channel (int): The MIDI channel.
        """
        cc = mido.Message("control_change", control=control, value=value, channel=channel)
        self._midi_out.send(cc)

    def pc(self, program: int = 0, channel: int = 1) -> None:
        """Send a MIDI program change message.

        Args:
            program (int): The program number.
            channel (int): The MIDI channel.
        """
        pc = mido.Message("program_change", program=program, channel=channel)
        self._midi_out.send(pc)

    def sysex(self, data: list) -> None:
        """Send a MIDI system exclusive message.

        Args:
            data (list): The sysex data.
        """
        sysex = mido.Message("sysex", data=data)
        self._midi_out.send(sysex)
