from .configuration import read_configuration, open_config_folder
from .utils import BASTON_LOGO, info_message, greeter
from .time.clock import Clock
from .io.midi import MIDIOut, MIDIIn, list_midi_ports
from .io.osc import OSC
from .environment import Environment
import functools

CONFIGURATION = read_configuration()
env = Environment()
clock = Clock(CONFIGURATION["tempo"])
env.subscribe(clock)

if CONFIGURATION["midi_out_port"] != "disabled":
    midi = MIDIOut(CONFIGURATION["midi_out_port"], clock)
    env.subscribe(midi)
else:
    info_message("No MIDI output port specified. MIDI is disabled.")

if CONFIGURATION["midi_in_port"] != "disabled":
    midi_in = MIDIIn(CONFIGURATION["midi_in_port"], clock)
    env.subscribe(midi_in)
else:
    info_message("No MIDI input port specified. MIDI input is disabled.")

c = clock
now = lambda: clock.beat
silence = clock.clear

osc = OSC("Test OSC Loop", "127.0.0.1", 57120)

def fight(quant="bar"):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        if quant == "bar":
            info_message(f"Starting [red]{func.__name__}[/red] on next bar")
            clock.add(func, clock.next_bar())
        elif quant == "beat":
            info_message(f"Starting [red]{func.__name__}[/red] on next beat")
            clock.add(func, clock.beat + 1)
        elif quant == "now":
            info_message(f"Starting [red]{func.__name__}[/red] now")
            clock.add(func, clock.beat)
        elif isinstance(quant, (int, float)):
            info_message(f"Starting [red]{func.__name__}[/red] in {quant} beats")
            clock.add(func, clock.beat + quant)
        else:
            raise ValueError(
                "Invalid quantization option. Choose 'bar', 'beat', 'now', or a numeric value."
            )
        return wrapper

    return decorator


def exit():
    """Exit the interactive shell"""
    env.dispatch(env, "exit", {})
    raise SystemExit

greeter()

clock.start()
clock.play()