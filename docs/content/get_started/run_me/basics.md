---
title: 1) Basics
tag: tutorial
---

This tutorial covers the following topics:
- **MIDI notes** using the `note()` [Sender](/reference/senders)
    - **note**: the MIDI note to play
    - **velocity**: the amplitude of the note
    - **length**: the duration of the note
- Writing rhythms and durations:
    - **period** (`p`): the period of the note
    - **rests**: writing silences with [Rest](/reference/patterns/Rest)
- A bunch of basic [Patterns](/reference/patterns) to generate sequences of values:
    - [Pseq](/reference/patterns/Pseq): a sequence of values
    - [Pnote](/reference/patterns/Pnote): a sequence of notes
    - [Peuclid](/reference/patterns/Peuclid): euclidian rhythm generator
    - [Psine](/reference/patterns/Psine): a sine wave generator
    - [Pexp](/reference/patterns/Pexp): an exponential generator
    - [Pchoose](/reference/patterns/Pchoose): a random choice generator
- The `silence()` function to stop all Players
```python
from shrimp import *

# Playing a note
p1 >> note(50)

# Playing a sequence of notes
p1 >> note(Pseq(50, 55, 57, 60))

# Changing the amplitude of each note

p1 >> note(
    note=Pseq(50, 55, 57, 60),
    vel=Pchoose(50, 100, 80),
)

# Changing the duration of each note
p1 >> note(
    note=Pseq(50, 55, 57, 60),
    vel=Pexp(min=50, max=100, n=15),
    p=Pseq(1, 1/2, 1/4, 1/4)
)

# Changing note length
p1 >> note(
    note=Pseq(50, 55, 57, 60),
    vel=Pexp(min=50, max=100, n=15),
    p=Pseq(1, 1/2),
    len=Pseq(1/4, 1/4, 1/2, 2),
)

# Adding silence
p1 >> note(
    note=Pseq(50, 55, 57, 60),
    p=Pseq(1, R(2), 1, 1/2, 1/2),
    vel=80, len=1,
)

# Using notes from a scale
p1 >> note(
    note=Pnote(-5, -3, -2, 0, 2, 4).mirror(),
    vel=Psine(freq=1, min=70, max=110),
    p=1/4, len=1/16,
)

# Using a rhythm generator
p1 >> note(
    note=Pnote(0, 2, 4, 0, 3, 5),
    p=Peuclid(5, 8) / 4, len=1/4,
)

# Adding another pattern
p1 >> note(
    note=Pnote(0, 2, 4, 0, 3, 5),
    p=Peuclid(5, 8) / 4, len=1/4,
)
p2 >> note(
    note=Pnote(0, 5, 10, 12, 0, 3, 7, 9),
    p=Peuclid(4, 8) / 4, len=8,
)

# Stopping all Players
silence()

# Alternatively (more selective):
silence(p1, p2)
```