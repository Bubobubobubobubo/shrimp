from .configuration import read_configuration
from .clock import Clock 
from .midi import MIDI
import code

CONFIGURATION = read_configuration()
clock = Clock(CONFIGURATION["tempo"])
midi = MIDI(CONFIGURATION["midi_port"], clock)
clock.start()
now = clock.beat

def exit():
    """Exit the interactive shell"""
    clock.stop()
    raise SystemExit

def dada():
    """Print the current clock state"""
    print(f"Bar: {clock.bar}, Beat: {clock.beat}, Phase: {clock.phase}, Tempo: {clock.tempo}")
    clock.add(clock.beat + 1, dada)

def bip():
    """Play a note"""
    from random import randint, choice
    midi.note(randint(30, 60), 100, 1, 1)
    clock.add(clock.beat + choice([1/2, 1, 2]), bip)

if __name__ == "__main__":
    code.interact(
        local=locals(),
        banner="Welcome to the Baston interactive shell!", 
        exitmsg="Goodbye!"
    )
    exit()