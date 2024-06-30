from .configuration import read_configuration, open_config_folder
from .utils import BASTON_LOGO, info_message, greeter
from .time.clock import Clock
from .io.midi import MIDIOut, MIDIIn, list_midi_ports
from .io.osc import OSC
from .environment import Environment
import functools

CONFIGURATION = read_configuration()
env = Environment()
clock = Clock(CONFIGURATION["clock"]["default_tempo"], CONFIGURATION["clock"]["time_grain"])
env.subscribe(clock)

# Opening MIDI output ports based on user configuration
for midi_out_port_name, port in CONFIGURATION["midi"]["out_ports"].items():
    if port is not False:
        info_message(f"Opening MIDI output: {port}. Variable: [red]{midi_out_port_name}[/red]", True)
        globals()[midi_out_port_name] = MIDIOut(port, clock)
        env.subscribe(globals()[midi_out_port_name])

# Opening MIDI input ports based on user configuration
for midi_in_port_name, port in CONFIGURATION["midi"]["in_ports"].items():
    if port is not False:
        info_message(f"Opening MIDI input: {port}, Variable: [red]{midi_in_port_name}", True)
        globals()[midi_in_port_name] = MIDIIn(port, clock)
        env.subscribe(globals()[midi_in_port_name])

# Opening OSC connexions based on user configuration
for osc_port_name, port in CONFIGURATION["osc"]["ports"].items():
    info_message(f"Opening OSC port: {port['host']}:{port['port']}, Variable: [red]{osc_port_name}[/red]", True)
    globals()[osc_port_name] = OSC(name=osc_port_name, host=port["host"], port=port["port"], clock=clock)
    env.subscribe(globals()[osc_port_name])

c = clock
now = lambda: clock.beat
next_bar = lambda: clock.next_bar
silence = clock.clear
loop = clock.add
stop = clock.remove

def loop_now(quant="bar"):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        if quant == "bar":
            info_message(f"Starting [red]{func.__name__}[/red] on next bar")
            clock.add(func, clock.next_bar)
        elif quant == "beat":
            info_message(f"Starting [red]{func.__name__}[/red] on next beat")
            clock.add(func, clock.next_beat)
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