from .configuration import read_configuration
from .utils import BASTON_LOGO, info_message, greeter
from .clock import Clock 
from .midi import MIDIOut, MIDIIn
from .environment import Environment
import functools

CONFIGURATION = read_configuration()
env = Environment()
clock = Clock(CONFIGURATION["tempo"])
env.subscribe(clock)
midi = MIDIOut(CONFIGURATION["midi_out_port"], clock)
env.subscribe(midi)
midi_in = MIDIIn(CONFIGURATION["midi_in_port"], clock)
env.subscribe(midi_in)
c = clock
now = lambda: clock.beat
silence = clock.clear
# The monitoring loop is blocking exit...
# clock.add(now, midi_in._monitoring_loop)

def fight(quant='bar'):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        if quant == 'bar':
            info_message(f"Starting [red]{func.__name__}[/red] on next bar")
            clock.add(func, clock.next_bar())
        elif quant == 'beat':
            info_message(f"Starting [red]{func.__name__}[/red] on next beat")
            clock.add(func, clock.beat + 1)
        elif quant == 'now':
            info_message(f"Starting [red]{func.__name__}[/red] now")
            clock.add(func, clock.beat)
        elif isinstance(quant, (int, float)):
            info_message(f"Starting [red]{func.__name__}[/red] in {quant} beats")
            clock.add(func, clock.beat + quant)
        else:
            raise ValueError("Invalid quantization option. Choose 'bar', 'beat', 'now', or a numeric value.")
        return wrapper
    return decorator

def exit():
    """Exit the interactive shell"""
    clock.stop()
    raise SystemExit

greeter()
clock.start()