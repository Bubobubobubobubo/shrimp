from .systems.Players.Player import Player

from signalflow import (
    SineOscillator,
    Patch,
    WhiteNoise,
    Add,
    Line,
    AudioGraph,
    ASREnvelope,
)


graph = AudioGraph()
