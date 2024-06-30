from baston import *
from random import randint
from itertools import cycle

if midi is None:
    print("A midi port named 'midi' is required to play this example! See configuration.")
    exit()

arpeggio = cycle([60, 63, 67, 70])

def playing_midi_notes(count= 0):
    """Playing an arpeggio (eight notes)"""
    if count == 16:
        exit()

    midi.note(note=next(arpeggio), velocity=randint(80, 100), duration=0.1)
    loop(playing_midi_notes, clock.now + (clock.beat_duration / 2), count=count + 1)

# Starting the recursive loop
loop(playing_midi_notes)