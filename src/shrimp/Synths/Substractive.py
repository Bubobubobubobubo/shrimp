from signalflow import (
    Patch,
    ASREnvelope,
    SawOscillator,
    StereoPanner,
    MoogVCF,
    ChannelMixer,
)
from .Utils import _note_to_freq, graph
from ..systems.PlayerSystem import PatternPlayer
from random import random


class MultiSaw(Patch):
    """A simple saw wave generator with an ASR envelope"""

    def __init__(
        self,
        note=None,
        attack: float = 0.0,
        sustain: float = 0,
        release: float = 0.1,
        frequency: float = 440,
        cutoff: float = 1000,
        resonance: float = 0.5,
        detune: float = 0.99,
        phase: float = 0.0,
        pan: float = 0.0,
        amp: float = 0.5,
        *args,
        **kwargs,
    ):
        super().__init__()
        attack = self.add_input("attack", attack)
        sustain = self.add_input("sustain", sustain)
        release = self.add_input("release", release)
        frequency = self.add_input("frequency", frequency)
        phase = self.add_input("phase", phase)
        pan = self.add_input("pan", pan)
        if note is not None:
            frequency = _note_to_freq(note)
        saw = SawOscillator(frequency, phase + min(0, max(random(), 1)))
        detuned_saw = SawOscillator(frequency * detune, phase)
        filter = MoogVCF(
            ChannelMixer(num_channels=1, input=[saw, detuned_saw], amplitude_compensation=True),
            cutoff,
            resonance,
        )
        envelope = ASREnvelope(attack, sustain, release)
        output = filter * envelope * amp
        output = StereoPanner(output, pan)
        self.auto_free = True
        self.set_output(output)


def multisaw(*args, **kwargs):
    test = lambda *a, **k: graph.play(MultiSaw(*a, **k))
    return PatternPlayer.Player._play_factory(
        test,
        *args,
        manual_polyphony=True,
        **kwargs,
    )
