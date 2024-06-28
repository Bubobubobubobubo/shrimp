# Baston

## Play a note

```python
def bip():
    """Play a note"""
    from random import randint, choice
    midi.note(randint(30, 60), 100, 1, 1)
    clock.add(clock.beat + choice([1/2, 1, 2]), bip)
```

and then

```python
clock.add(now, bip)
```

To make sure that the playback starts on the beat, make sure to truncate `clock.beat` to the nearest beat (integer).
