from signalflow import (
    Patch,
    SineOscillator,
    WhiteNoise,
    ASREnvelope,
    Add,
    Line,
    StereoPanner,
    SVFilter,
)
from ..systems.PlayerSystem import PatternPlayer
from .Utils import graph


class Kick(Patch):
    def __init__(
        self, attack=0, sustain=0, release=0.1, frequency=80, pan=0.0, amp=0.5, *args, **kwargs
    ):
        super().__init__()
        attack = self.add_input("attack", attack)
        sustain = self.add_input("sustain", sustain)
        release = self.add_input("release", release)
        frequency = self.add_input("frequency", frequency)
        pan = self.add_input("pan", pan)
        freq_line = Line(start=frequency * 2, end=frequency / 2, time=release / 2)
        amp_line = Line(start=1, end=0, time=release / 2)
        sine = SineOscillator(freq_line)
        noise = WhiteNoise() * amp_line * 0.25
        envelope = ASREnvelope(attack, sustain, release)
        output = sine * envelope * amp
        output = StereoPanner(output, pan)
        self.auto_free = True
        self.set_output(output)


class HiHat(Patch):
    def __init__(self, attack=0, sustain=0, release=0.1, pan=0.0, amp=0.5, *args, **kwargs):
        super().__init__()
        attack = self.add_input("attack", attack)
        sustain = self.add_input("sustain", sustain)
        release = self.add_input("release", release)
        pan = self.add_input("pan", pan)
        # Definition starts here
        noise = WhiteNoise()
        filtered = SVFilter(input=noise, filter_type="high_pass", cutoff=5000, resonance=0.6)
        envelope = ASREnvelope(attack, sustain, release)
        output = filtered * envelope * amp
        output = StereoPanner(output, pan)
        self.auto_free = True
        self.set_output(output)


class Noise(Patch):
    """A simple noise generator with an ASR envelope."""

    def __init__(self, attack=0.0, sustain=0, release=0.1, pan=0.0, amp=0.5, *args, **kwargs):
        super().__init__()
        attack = self.add_input("attack", attack)
        sustain = self.add_input("sustain", sustain)
        release = self.add_input("release", release)
        pan = self.add_input("pan", pan)
        noise = WhiteNoise()
        envelope = ASREnvelope(attack, sustain, release)
        output = noise * envelope * amp
        output = StereoPanner(output, pan)
        self.auto_free = True
        self.set_output(output)


def kick(*args, **kwargs):
    test = lambda *a, **k: graph.play(Kick(*a, **k))
    return PatternPlayer.Player._play_factory(test, *args, **kwargs)


def noise(*args, **kwargs):
    test = lambda *a, **k: graph.play(Noise(*a, **k))
    return PatternPlayer.Player._play_factory(test, *args, **kwargs)


def hat(*args, **kwargs):
    test = lambda *a, **k: graph.play(HiHat(*a, **k))
    return PatternPlayer.Player._play_factory(test, *args, **kwargs)
