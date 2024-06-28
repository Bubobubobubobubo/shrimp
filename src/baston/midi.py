import mido
from .clock import Clock

class MIDI:

    """MIDI class to send MIDI messages to a MIDI port."""

    def __init__(self, port: str, clock: Clock):
        self.port = port
        self.clock = clock
        try:
            self._midi_out = mido.open_output(port)
        except:
            print(f"Could not open MIDI port {port}")

    def _note_on(self, note: int = 60, velocity: int = 100, channel: int = 1) -> None:
        """Send a MIDI note on message:

        Args:
            note (int): The MIDI note number.
            velocity (int): The velocity of the note.
            channel (int): The MIDI channel.

        """
        note = mido.Message('note_on', note=note, velocity=velocity, channel=channel)
        self._midi_out.send(note)

    def _note_off(self, note: int = 60, velocity: int = 0, channel: int = 1) -> None:
        """Send a MIDI note off message.

        Args:
            note (int): The MIDI note number.
            velocity (int): The velocity of the note.
            channel (int): The MIDI channel.
        """
        note = mido.Message('note_off', note=note, velocity=velocity, channel=channel)
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
        self.clock.add(self.clock.beat, lambda: self._note_on(note, velocity, channel))
        self.clock.add(self.clock.beat + duration, lambda: self._note_off(note, 0, channel))

    def cc(self, control: int = 0, value: int = 0, channel: int = 1) -> None:
        """Send a MIDI control change message.
        
        Args:
            control (int): The control number.
            value (int): The control value.
            channel (int): The MIDI channel.
        """
        cc = mido.Message('control_change', control=control, value=value, channel=channel)
        self._midi_out.send(cc)

    def pc(self, program: int = 0, channel: int = 1) -> None:
        """Send a MIDI program change message.

        Args:
            program (int): The program number.
            channel (int): The MIDI channel.
        """
        pc = mido.Message('program_change', program=program, channel=channel)
        self._midi_out.send(pc)

    def sysex(self, data: list) -> None:
        """Send a MIDI system exclusive message.
        
        Args:
            data (list): The sysex data.
        """
        sysex = mido.Message('sysex', data=data)
        self._midi_out.send(sysex)