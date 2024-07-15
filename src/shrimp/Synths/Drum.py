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
from ..utils import alias_param


class Kick(Patch):
    def __init__(
        self, attack=0, sustain=0, release=0.1, freq=80, pan=0.0, amp=0.25, *args, **kwargs
    ):
        super().__init__()
        attack = self.add_input("attack", attack)
        sustain = self.add_input("sustain", sustain)
        release = self.add_input("release", release)
        freq = self.add_input("freq", freq)
        pan = self.add_input("pan", pan)
        freq_line = Line(start=freq * 2, end=freq / 2, time=release / 2)
        amp_line = Line(start=1, end=0, time=release / 2)
        sine = SineOscillator(freq_line)
        noise = WhiteNoise() * amp_line * 0.25
        envelope = ASREnvelope(attack, sustain, release)
        output = sine * envelope * amp
        output = StereoPanner(output, pan)
        self.auto_free = True
        self.set_output(output)


class Snare(Patch):
    def __init__(
        self,
        freq=180,
        attack=0,
        sustain=0,
        release=0.1,
        cutoff=2000,
        pan=0.0,
        amp=0.25,
        *args,
        **kwargs,
    ):
        super().__init__()
        freq = self.add_input("freq", freq)
        attack = self.add_input("attack", attack)
        sustain = self.add_input("sustain", sustain)
        release = self.add_input("release", release)
        pan = self.add_input("pan", pan)
        env = ASREnvelope(attack=attack, sustain=sustain, release=release, curve=2)
        snd = WhiteNoise()
        snd = SVFilter(snd, filter_type="high_pass", cutoff=cutoff)
        sine = SineOscillator(freq)
        output = Add(snd, sine) * env * amp
        output = StereoPanner(output, pan)
        self.auto_free = True
        self.set_output(output)


class HiHat(Patch):
    def __init__(
        self, attack=0, sustain=0, release=0.1, pan=0.0, amp=0.25, cutoff=8000, *args, **kwargs
    ):
        super().__init__()
        attack = self.add_input("attack", attack)
        sustain = self.add_input("sustain", sustain)
        release = self.add_input("release", release)
        cutoff = self.add_input("cutoff", cutoff)
        pan = self.add_input("pan", pan)
        # Definition starts here
        noise = WhiteNoise()
        filtered = SVFilter(input=noise, filter_type="high_pass", cutoff=cutoff, resonance=0.6)
        envelope = ASREnvelope(attack, sustain, release / 2, curve=2)
        output = filtered * envelope * amp
        output = StereoPanner(output, pan)
        self.auto_free = True
        self.set_output(output)


class Noise(Patch):
    """A simple noise generator with an ASR envelope."""

    def __init__(self, attack=0.0, sustain=0, release=0.1, pan=0.0, amp=0.25, *args, **kwargs):
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


@alias_param("period", "p")
def kick(*args, **kwargs):
    test = lambda *a, **k: graph.play(Kick(*a, **k))
    return PatternPlayer.Player._play_factory(test, *args, **kwargs)


@alias_param("period", "p")
def noise(*args, **kwargs):
    test = lambda *a, **k: graph.play(Noise(*a, **k))
    return PatternPlayer.Player._play_factory(test, *args, **kwargs)


@alias_param("period", "p")
def hat(*args, **kwargs):
    test = lambda *a, **k: graph.play(HiHat(*a, **k))
    return PatternPlayer.Player._play_factory(test, *args, **kwargs)


@alias_param("period", "p")
def snare(*args, **kwargs):
    test = lambda *a, **k: graph.play(Snare(*a, **k))
    return PatternPlayer.Player._play_factory(test, *args, **kwargs)
