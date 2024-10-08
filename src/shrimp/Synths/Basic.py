from itertools import cycle, islice
from random import random
from ..Systems.PlayerSystem import PatternPlayer
from ..utils import alias_param
from signalflow import (
    SineOscillator,
    SVFilter,
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
        attack: float = 0.0,
        sustain: float = 0,
        release: float = 0.1,
        curve: float = 1,
        freq: float = 440,
        pan: float = 0.0,
        amp: float = 0.25,
        cutoff: float = 18000,
        filter_type: str = "low_pass",
        vib: float = 6.0,
        vib_depth: float = 0.0,
        resonance: float = 0.5,
        *args,
        **kwargs,
    ):
        super().__init__()
        attack = self.add_input("attack", attack)
        sustain = self.add_input("sustain", sustain)
        release = self.add_input("release", release)
        freq = self.add_input("freq", freq)
        pan = self.add_input("pan", pan)
        amp = self.add_input("amp", amp)
        vibrato = self.add_input("vib", vib)
        vibrato = self.add_input("vib_depth", vib_depth)
        if note is not None:
            freq = _note_to_freq(note)
        sine = SineOscillator(freq + (SineOscillator(vib) * vib_depth))
        envelope = ASREnvelope(attack, sustain, release, curve=curve)
        output = sine * envelope * amp
        output = SVFilter(input=output, filter_type=filter_type, cutoff=cutoff, resonance=resonance)
        output = StereoPanner(output, pan)
        self.auto_free = True
        self.set_output(output)


class FM(Patch):
    """A simple sine wave generator with an ASR envelope."""

    def __init__(
        self,
        note=None,
        attack: float = 0.0,
        sustain: float = 0,
        release: float = 0.1,
        curve: float = 1,
        freq: float = 440,
        pan: float = 0.0,
        amp: float = 0.25,
        depth: float = 1.0,
        ratio: float = 1.0,
        cutoff: float = 18000,
        resonance: float = 0.5,
        filter_type: str = "low_pass",
        vib: float = 6.0,
        vib_depth: float = 0.0,
        *args,
        **kwargs,
    ):
        super().__init__()
        attack = self.add_input("attack", attack)
        sustain = self.add_input("sustain", sustain)
        release = self.add_input("release", release)
        freq = self.add_input("freq", freq)
        mod_ratio = self.add_input("mod_ratio", ratio)
        mod_depth = self.add_input("mod_depth", depth)
        pan = self.add_input("pan", pan)
        amp = self.add_input("amp", amp)
        if note is not None:
            freq = _note_to_freq(note)
        modulator = (
            SineOscillator((freq + (SineOscillator(vib) * vib_depth)) * mod_ratio) * mod_depth
        )
        carrier = SineOscillator((freq + (SineOscillator(vib) * vib_depth)) * modulator)
        envelope = ASREnvelope(attack=attack, sustain=sustain, release=release, curve=curve)
        output = carrier * envelope * amp

        output = SVFilter(input=output, filter_type=filter_type, cutoff=cutoff, resonance=resonance)
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
        curve: float = 1,
        freq: float = 440,
        pan: float = 0.0,
        amp: float = 0.5,
        harmonics: int = 4,
        amplitudes: list = [1],
        deviation: float = 0.0,
        cutoff: float = 18000,
        resonance: float = 0.5,
        filter_type: str = "low_pass",
        vib: float = 6.0,
        vib_depth: float = 0.0,
        *args,
        **kwargs,
    ):
        super().__init__()
        if not isinstance(amplitudes, list):
            amplitudes = [amplitudes]
        attack = self.add_input("attack", attack)
        sustain = self.add_input("sustain", sustain)
        release = self.add_input("release", release)
        freq = self.add_input("freq", freq)
        pan = self.add_input("pan", pan)
        amp = self.add_input("amp", amp)
        if note is not None:
            freq = _note_to_freq(note)
        note_harmonics = [
            freq + (SineOscillator(vib) * vib_depth) * _ + ((random() * deviation) * freq)
            for _ in range(harmonics)
        ]
        oscillator = SineOscillator(note_harmonics) * list(islice(cycle(amplitudes), harmonics))
        envelope = ASREnvelope(attack=attack, sustain=sustain, release=release, curve=curve)
        output = oscillator * envelope * amp
        output = ChannelMixer(num_channels=1, input=output, amplitude_compensation=True)
        output = SVFilter(input=output, filter_type=filter_type, cutoff=cutoff, resonance=resonance)
        output = StereoPanner(output, pan)
        self.auto_free = True
        self.set_output(output)


class Square(Patch):
    """A simple square wave generator with an ASR envelope."""

    def __init__(
        self,
        note=None,
        attack: float = 0.0,
        sustain: float = 0,
        release: float = 0.1,
        curve: float = 1,
        freq: float = 440,
        width: float = 0.5,
        cutoff: float = 18000,
        resonance: float = 0.5,
        pan: float = 0.0,
        amp: float = 0.25,
        filter_type: str = "low_pass",
        vib: float = 6.0,
        vib_depth: float = 0.0,
        *args,
        **kwargs,
    ):
        super().__init__()
        attack = self.add_input("attack", attack)
        sustain = self.add_input("sustain", sustain)
        release = self.add_input("release", release)
        width = self.add_input("width", width)
        freq = self.add_input("freq", freq)
        pan = self.add_input("pan", pan)
        amp = self.add_input("pan", amp)
        if note is not None:
            freq = _note_to_freq(note)
        square = SquareOscillator(freq + (SineOscillator(vib) * vib_depth), width)
        envelope = ASREnvelope(attack=attack, sustain=sustain, release=release, curve=curve)
        output = square * envelope * amp

        output = SVFilter(input=output, filter_type=filter_type, cutoff=cutoff, resonance=resonance)
        output = StereoPanner(output, pan)
        self.auto_free = True
        self.set_output(output)


class Triangle(Patch):
    """A simple triangle wave generator with an ASR envelope."""

    def __init__(
        self,
        note=None,
        attack: float = 0.0,
        sustain: float = 0,
        release: float = 0.1,
        curve: float = 1,
        freq: float = 440,
        pan: float = 0.0,
        amp: float = 0.25,
        cutoff: float = 18000,
        resonance: float = 0.5,
        filter_type: str = "low_pass",
        vib: float = 6.0,
        vib_depth: float = 0.0,
        *args,
        **kwargs,
    ):
        super().__init__()
        attack = self.add_input("attack", attack)
        sustain = self.add_input("sustain", sustain)
        release = self.add_input("release", release)
        freq = self.add_input("freq", freq)
        pan = self.add_input("pan", pan)
        if note is not None:
            freq = _note_to_freq(note)
        triangle = TriangleOscillator(freq + (SineOscillator(vib) * vib_depth))
        envelope = ASREnvelope(attack=attack, sustain=sustain, release=release, curve=curve)
        output = triangle * envelope * amp

        output = SVFilter(input=output, filter_type=filter_type, cutoff=cutoff, resonance=resonance)
        output = StereoPanner(output, pan)
        self.auto_free = True
        self.set_output(output)


class Saw(Patch):
    """A simple saw wave generator with an ASR envelope"""

    def __init__(
        self,
        note=None,
        attack: float = 0.0,
        sustain: float = 0,
        release: float = 0.1,
        curve: float = 1,
        freq: float = 440,
        phase: float = 0.0,
        pan: float = 0.0,
        amp: float = 0.0,
        cutoff: float = 18000,
        resonance: float = 0.5,
        filter_type: str = "low_pass",
        vib: float = 6.0,
        vib_depth: float = 0.0,
        *args,
        **kwargs,
    ):
        super().__init__()
        attack = self.add_input("attack", attack)
        sustain = self.add_input("sustain", sustain)
        release = self.add_input("release", release)
        freq = self.add_input("freq", freq)
        phase = self.add_input("phase", phase)
        pan = self.add_input("pan", pan)
        if note is not None:
            freq = _note_to_freq(note)
        sine = SawOscillator(freq + (SineOscillator(vib) * vib_depth), phase)
        envelope = ASREnvelope(attack=attack, sustain=sustain, release=release, curve=curve)
        output = sine * envelope * amp
        output = SVFilter(input=output, filter_type=filter_type, cutoff=cutoff, resonance=resonance)
        output = StereoPanner(output, pan)
        self.auto_free = True
        self.set_output(output)


# @alias_param("period", "p")
# def sine(*args, **kwargs):
#     test = lambda *a, **k: graph.play(Sine(*a, **k))
#     return PatternPlayer.Player._play_factory(test, *args, manual_polyphony=True, **kwargs)
synth_sine = lambda *a, **k: graph.play(Sine(*a, **k))


# @alias_param("period", "p")
# def square(*args, **kwargs):
#     test = lambda *a, **k: graph.play(Square(*a, **k))
#     return PatternPlayer.Player._play_factory(
#         test,
#         *args,
#         manual_polyphony=True,
#         **kwargs,
#     )
synth_square = lambda *a, **k: graph.play(Square(*a, **k))


# @alias_param("period", "p")
# def triangle(*args, **kwargs):
#     test = lambda *a, **k: graph.play(Triangle(*a, **k))
#     return PatternPlayer.Player._play_factory(test, *args, manual_polyphony=True, **kwargs)
synth_triangle = lambda *a, **k: graph.play(Triangle(*a, **k))


# @alias_param("period", "p")
# def saw(*args, **kwargs):
#     test = lambda *a, **k: graph.play(Saw(*a, **k))
#     return PatternPlayer.Player._play_factory(
#         test,
#         *args,
#         manual_polyphony=True,
#         **kwargs,
#     )
synth_saw = lambda *a, **k: graph.play(Saw(*a, **k))

# @alias_param("period", "p")
# def fm2(*args, **kwargs):
#     test = lambda *a, **k: graph.play(FM(*a, **k))
#     return PatternPlayer.Player._play_factory(
#         test,
#         *args,
#         manual_polyphony=True,
#         **kwargs,
#     )
synth_fm2 = lambda *a, **k: graph.play(FM(*a, **k))


# @alias_param("period", "p")
# def add(*args, **kwargs):
#     test = lambda *a, **k: graph.play(Additive(*a, **k))
#     return PatternPlayer.Player._play_factory(
#         test,
#         *args,
#         manual_polyphony=True,
#         **kwargs,
#     )
synth_add = lambda *a, **k: graph.play(Additive(*a, **k))
