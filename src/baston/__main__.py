from .configuration import read_configuration
from .utils import BASTON_LOGO, info_message, greeter
from .clock import Clock 
from .midi import MIDIOut, MIDIIn
import functools
import code

CONFIGURATION = read_configuration()
clock = Clock(CONFIGURATION["tempo"])
midi = MIDIOut(CONFIGURATION["midi_out_port"], clock)
midi_in = MIDIIn(CONFIGURATION["midi_in_port"], clock)
c = clock
now = lambda: clock.beat
# The monitoring loop is blocking exit...
# clock.add(now, midi_in._monitoring_loop)

def fight(quant='bar'):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        if quant == 'bar':
            info_message(f"Starting [red]{func.__name__}[/red] on next bar")
            clock.add(clock.next_bar(), func)
        elif quant == 'beat':
            info_message(f"Starting [red]{func.__name__}[/red] on next beat")
            clock.add(clock.beat + 1, func)
        elif quant == 'now':
            info_message(f"Starting [red]{func.__name__}[/red] now")
            clock.add(clock.beat, func)
        elif isinstance(quant, (int, float)):
            info_message(f"Starting [red]{func.__name__}[/red] in {quant} beats")
            clock.add(clock.beat + quant, func)
        else:
            raise ValueError("Invalid quantization option. Choose 'bar', 'beat', 'now', or a numeric value.")
        return wrapper
    return decorator

# TODO: why does it repeat the function?
def stop(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        clock.remove(func)
        return func(*args, **kwargs)
    return wrapper

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
    midi.note(72 if int(clock.beat % clock._denominator) == 0 else 48, 100, 1, 1)
    clock.add(int(clock.beat) + 1, bip)

if __name__ == "__main__":
    clock.start()
    greeter()
    code.interact(
        local=locals(),
        banner="", 
        exitmsg="Goodbye!"
    )
    exit()