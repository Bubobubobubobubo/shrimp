from .configuration import read_configuration, open_config_folder
from .utils import info_message, greeter
from .time.clock import Clock, TimePos
from functools import partial
from .io.midi import MIDIOut, MIDIIn, list_midi_ports
from .io.osc import OSC
from rich import print
from .environment import get_global_environment
from .systems.PlayerSystem.Pattern import *
from .systems.PlayerSystem.Library import *
from .systems.PlayerSystem.PatternPlayer import Player
from .systems.PlayerSystem.GlobalConfig import global_config as PlayerConfig
import functools
import os

# Do not import signalflow if on Linux or Windows!
current_os = os.uname().sysname
if current_os == "Darwin":
    from .Synths import *

CONFIGURATION = read_configuration()

if CONFIGURATION["editor"]["greeter"]:
    greeter()

env = get_global_environment()
clock = Clock(
    tempo=CONFIGURATION["clock"]["default_tempo"],
    grain=CONFIGURATION["clock"]["time_grain"],
    delay=int(CONFIGURATION["clock"]["delay"]),
)
env.add_clock(clock)
pattern = Player.initialize_patterns(clock)

# Opening MIDI output ports based on user configuration
for all_output_midi_ports in CONFIGURATION["midi"]["out_ports"]:
    for midi_out_port_name, port in all_output_midi_ports.items():
        if midi_out_port_name != "instruments" and port:
            if CONFIGURATION["editor"]["greeter"]:
                print(
                    f"[bold yellow]> MIDI Output [red]{midi_out_port_name}[/red] added for port: [red]{port}[/red] [/bold yellow]"
                )
            globals()[midi_out_port_name] = MIDIOut(port, clock)
            env.subscribe(globals()[midi_out_port_name])

            # Declaring new MIDI instruments
            instruments = all_output_midi_ports.get("instruments", [])
            for instrument in instruments:
                name = instrument["name"]
                channel = instrument["channel"]
                new_instrument = globals()[midi_out_port_name].make_instrument(
                    channel, instrument["control_map"]
                )
                globals()[name] = new_instrument
                if CONFIGURATION["editor"]["greeter"]:
                    print(f"[bold yellow]> MIDI Instrument added: [red]{name}[/red] [/bold yellow]")

            # Declaring new MIDI controllers
            controllers = all_output_midi_ports.get("controllers", [])
            for controller in controllers:
                name = controller["name"]
                new_controller = globals()[midi_out_port_name].make_controller(
                    controller["control_map"]
                )
                globals()[name] = new_controller
                if CONFIGURATION["editor"]["greeter"]:
                    print(f"[bold yellow]> MIDI Controller added: [red]{name}[/red] [/bold yellow]")


# Opening MIDI input ports based on user configuration
for midi_in_port_name, port in CONFIGURATION["midi"]["in_ports"].items():
    if port is not False:
        if CONFIGURATION["editor"]["greeter"]:
            print(
                f"[bold yellow]> MIDI Output [red]{midi_in_port_name}[/red] added for port: [red]{port}[/red] [/bold yellow]"
            )
        globals()[midi_in_port_name] = MIDIIn(port, clock)
        env.subscribe(globals()[midi_in_port_name])

# Opening OSC connexions based on user configuration
for osc_port_name, port in CONFIGURATION["osc"]["ports"].items():
    if CONFIGURATION["editor"]["greeter"]:
        print(f"[bold yellow]> OSC Port added: [red]{osc_port_name}[/red] [/bold yellow]")
    globals()[osc_port_name] = OSC(
        name=osc_port_name, host=port["host"], port=port["port"], clock=clock
    )
    env.subscribe(globals()[osc_port_name])

c = clock
now = lambda: clock.beat
next_bar = lambda: clock.next_bar
on_next_bar = clock.add_on_next_bar
on_next_beat = clock.add_on_next_beat
loop = clock.add
loopr = partial(loop, relative=True)
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
    clock.stop()


clock.start()
clock.add(func=lambda: clock.play(now=True), time=clock.now, passthrough=True)

# == TEST AREA FOR THE PATTERN SYSTEM ======================================================


if globals().get("superdirt", None) is not None:
    superdirt = globals()["superdirt"]

    def dirt(*args, **kwargs):
        """Example use:

        >> aa * d(sound="bd", speed=2, amp=4)

        >> aa * None
        >> aa.stop()
        """
        return Player._play_factory(superdirt.player_dirt, *args, **kwargs)


if globals().get("midi", None) is not None:
    midi = globals()["midi"]

    def debug(*args, **kwargs):
        return Player._play_factory(pattern_printer, *args, **kwargs)

    def n(*args, **kwargs):
        return Player._play_factory(midi.note, *args, **kwargs)

    def cc(*args, **kwargs):
        return Player._play_factory(midi.control_change, *args, **kwargs)

    def pc(*args, **kwargs):
        return Player._play_factory(midi.program_change, *args, **kwargs)

    def bd(*args, **kwargs):
        return Player._play_factory(midi.pitch_bend, *args, **kwargs)

    def sy(*args, **kwargs):
        return Player._play_factory(midi.sysex, *args, **kwargs)

    if globals().get("kabelsalat_instrument", None) is not None:
        kabel = globals()["kabelsalat_instrument"]

        def kabelsalat(*args, **kwargs):
            return Player._play_factory(kabel, *args, **kwargs)


# Adding all patterns to the global scope
for key, value in pattern.items():
    globals()[key] = value


def silence():
    env.dispatch("main", "silence", {})
    for key in pattern.keys():
        globals()[key].stop()
    if "graph" in globals():
        graph.clear()
