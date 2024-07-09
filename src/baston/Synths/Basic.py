from itertools import cycle, islice
from random import random
from ..systems.PlayerSystem import PatternPlayer
from signalflow import (
    SineOscillator,
    Patch,
    SquareOscillator,
    ChannelMixer,
    TriangleOscillator,
    SawOscillator,
    ASREnvelope,
    StereoPanner,
)

from .Utils import _note_to_freq, graph


class Sine(Patch):
    """A simple sine wave generator with an ASR envelope."""

    def __init__(
        self,
        note=None,
        attack=0.0,
        sustain=0,
        release=0.1,
        frequency=440,
        pan=0.0,
        amp=0.5,
        *args,
        **kwargs,
    ):
        super().__init__()
        attack = self.add_input("attack", attack)
        sustain = self.add_input("sustain", sustain)
        release = self.add_input("release", release)
        frequency = self.add_input("frequency", frequency)
        pan = self.add_input("pan", pan)
        amp = self.add_input("amp", amp)
        if note is not None:
            frequency = _note_to_freq(note)
        sine = SineOscillator(frequency)
        envelope = ASREnvelope(attack, sustain, release)
        output = sine * envelope * amp
        output = StereoPanner(output, pan)
        self.auto_free = True
        self.set_output(output)


class FM(Patch):
    """A simple sine wave generator with an ASR envelope."""

    def __init__(
        self,
        note=None,
        attack=0.0,
        sustain=0,
        release=0.1,
        frequency=440,
        pan=0.0,
        amp=0.5,
        depth=1.0,
        ratio=1.0,
        *args,
        **kwargs,
    ):
        super().__init__()
        attack = self.add_input("attack", attack)
        sustain = self.add_input("sustain", sustain)
        release = self.add_input("release", release)
        frequency = self.add_input("frequency", frequency)
        mod_ratio = self.add_input("mod_ratio", ratio)
        mod_depth = self.add_input("mod_depth", depth)
        pan = self.add_input("pan", pan)
        amp = self.add_input("amp", amp)
        if note is not None:
            frequency = _note_to_freq(note)
        modulator = SineOscillator(frequency * mod_ratio) * mod_depth
        carrier = SineOscillator(frequency * modulator)
        envelope = ASREnvelope(attack, sustain, release)
        output = carrier * envelope * amp
        output = StereoPanner(output, pan)
        self.auto_free = True
        self.set_output(output)


class Additive(Patch):
    """A simple additive synthesizer with an ASR envelope."""

    def __init__(
        self,
        note: int = None,
        attack: float = 0.0,
        sustain: float = 0,
        release: float = 0.5,
        frequency: float = 440,
        pan: float = 0.0,
        amp: float = 0.5,
        harmonics: int = 4,
        amplitudes: list = [1],
        deviation: float = 0.0,
        *args,
        **kwargs,
    ):
        super().__init__()
        if not isinstance(amplitudes, list):
            amplitudes = [amplitudes]
        attack = self.add_input("attack", attack)
        sustain = self.add_input("sustain", sustain)
        release = self.add_input("release", release)
        frequency = self.add_input("frequency", frequency)
        pan = self.add_input("pan", pan)
        amp = self.add_input("amp", amp)
        if note is not None:
            frequency = _note_to_freq(note)
        note_harmonics = [
            frequency * _ + ((random() * deviation) * frequency) for _ in range(harmonics)
        ]
        oscillator = SineOscillator(note_harmonics) * list(islice(cycle(amplitudes), harmonics))
        envelope = ASREnvelope(attack, sustain, release)
        output = oscillator * envelope * amp
        output = ChannelMixer(num_channels=1, input=output, amplitude_compensation=True)
        output = StereoPanner(output, pan)
        self.auto_free = True
        self.set_output(output)


class Square(Patch):
    """A simple square wave generator with an ASR envelope."""

    def __init__(
        self,
        note=None,
        attack=0.0,
        sustain=0,
        release=0.1,
        frequency=440,
        width=0.5,
        pan=0.0,
        amp=0.5,
        *args,
        **kwargs,
    ):
        super().__init__()
        attack = self.add_input("attack", attack)
        sustain = self.add_input("sustain", sustain)
        release = self.add_input("release", release)
        width = self.add_input("width", width)
        frequency = self.add_input("frequency", frequency)
        pan = self.add_input("pan", pan)
        amp = self.add_input("pan", amp)
        if note is not None:
            frequency = _note_to_freq(note)
        square = SquareOscillator(frequency, width)
        envelope = ASREnvelope(attack, sustain, release)
        output = square * envelope * amp
        output = StereoPanner(output, pan)
        self.auto_free = True
        self.set_output(output)


class Triangle(Patch):
    """A simple triangle wave generator with an ASR envelope."""

    def __init__(
        self,
        note=None,
        attack=0.0,
        sustain=0,
        release=0.1,
        frequency=440,
        pan=0.0,
        amp=0.5,
        *args,
        **kwargs,
    ):
        super().__init__()
        attack = self.add_input("attack", attack)
        sustain = self.add_input("sustain", sustain)
        release = self.add_input("release", release)
        frequency = self.add_input("frequency", frequency)
        pan = self.add_input("pan", pan)
        if note is not None:
            frequency = _note_to_freq(note)
        triangle = TriangleOscillator(frequency)
        envelope = ASREnvelope(attack, sustain, release)
        output = triangle * envelope * amp
        output = StereoPanner(output, pan)
        self.auto_free = True
        self.set_output(output)


class Saw(Patch):
    """A simple saw wave generator with an ASR envelope"""

    def __init__(
        self,
        note=None,
        attack=0.0,
        sustain=0,
        release=0.1,
        frequency=440,
        phase=0.0,
        pan=0.0,
        amp=0.0,
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
        sine = SawOscillator(frequency, phase)
        envelope = ASREnvelope(attack, sustain, release)
        output = sine * envelope * amp
        output = StereoPanner(output, pan)
        self.auto_free = True
        self.set_output(output)


def sine(*args, **kwargs):
    test = lambda *a, **k: graph.play(Sine(*a, **k))
    return PatternPlayer.Player._play_factory(test, *args, manual_polyphony=True, **kwargs)


def square(*args, **kwargs):
    test = lambda *a, **k: graph.play(Square(*a, **k))
    return PatternPlayer.Player._play_factory(
        test,
        *args,
        manual_polyphony=True,
        **kwargs,
    )


def triangle(*args, **kwargs):
    test = lambda *a, **k: graph.play(Triangle(*a, **k))
    return PatternPlayer.Player._play_factory(test, *args, manual_polyphony=True, **kwargs)


def saw(*args, **kwargs):
    test = lambda *a, **k: graph.play(Saw(*a, **k))
    return PatternPlayer.Player._play_factory(
        test,
        *args,
        manual_polyphony=True,
        **kwargs,
    )


def fm2(*args, **kwargs):
    test = lambda *a, **k: graph.play(FM(*a, **k))
    return PatternPlayer.Player._play_factory(
        test,
        *args,
        manual_polyphony=True,
        **kwargs,
    )


def add(*args, **kwargs):
    test = lambda *a, **k: graph.play(Additive(*a, **k))
    return PatternPlayer.Player._play_factory(
        test,
        *args,
        manual_polyphony=True,
        **kwargs,
    )
