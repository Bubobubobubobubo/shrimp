import mido
from .clock import Clock

class MIDI:
    def __init__(self, port: str, clock: Clock):
        self.port = port
        self.clock = clock
        try:
            self._midi_out = mido.open_output(port)
        except:
            print(f"Could not open MIDI port {port}")

    def _note_on(self, note: int = 60, velocity: int = 100, channel: int = 1) -> mido.Message:
        note = mido.Message('note_on', note=note, velocity=velocity, channel=channel)
        self._midi_out.send(note)

    def _note_off(self, note: int = 60, velocity: int = 0, channel: int = 1) -> mido.Message:
        note = mido.Message('note_off', note=note, velocity=velocity, channel=channel)
        self._midi_out.send(note)

    def note(self, note: int = 60, velocity: int = 100, channel: int = 1, duration: int = 1):
        self.clock.add(self.clock.beat, lambda: self._note_on(note, velocity, channel))
        self.clock.add(self.clock.beat + duration, lambda: self._note_off(note, 0, channel))