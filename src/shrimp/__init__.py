import sys

sys.dont_write_bytecode = True

from .configuration import read_configuration, open_config_folder
from .utils import info_message, greeter, alias_param
from .Time.Clock import Clock
from functools import partial
from .IO.midi import MIDIOut, MIDIIn, list_midi_ports
from .IO.osc import OSC
from rich import print
from .environment import get_global_environment
import logging
import os

logging.warning("=========== Program start ==============")

# Do not import signalflow if on Linux or Windows!
current_os = os.uname().sysname
if current_os == "Darwin":
    from .Synths import *

CONFIGURATION = read_configuration()

if CONFIGURATION["editor"]["greeter"]:
    greeter()

env = get_global_environment()
if not env:
    raise Exception("Environment not found")

clock = Clock(
    tempo=CONFIGURATION["clock"]["default_tempo"],
    grain=CONFIGURATION["clock"]["time_grain"],
    delay=int(CONFIGURATION["clock"]["delay"]),
)
env.add_clock(clock)
# pattern = Player.initialize_patterns(clock)
# for pattern in pattern.values():
#     # Registering the pattern to the global environment
#     env.subscribe(pattern)

# Opening MIDI output ports based on user configuration
for all_output_midi_ports in CONFIGURATION["midi"]["out_ports"]:
    for midi_out_port_name, port in all_output_midi_ports.items():
        if midi_out_port_name != "instruments" and port:
            if CONFIGURATION["editor"]["greeter"]:
                logging.info(f"MIDI Output {midi_out_port_name} added for port: {port}")
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
                    logging.info(f"MIDI Instrument added: {name}")
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
                    logging.info(f"MIDI Controller added: {name}")
                    print(f"[bold yellow]> MIDI Controller added: [red]{name}[/red] [/bold yellow]")


# Opening MIDI input ports based on user configuration
for midi_in_port_name, port in CONFIGURATION["midi"]["in_ports"].items():
    if port is not False:
        if CONFIGURATION["editor"]["greeter"]:
            logging.info(f"MIDI Input {midi_in_port_name} added for port: {port}")
            print(
                f"[bold yellow]> MIDI Output [red]{midi_in_port_name}[/red] added for port: [red]{port}[/red] [/bold yellow]"
            )
        globals()[midi_in_port_name] = MIDIIn(port, clock)
        env.subscribe(globals()[midi_in_port_name])

# Opening OSC connexions based on user configuration
for osc_port_name, port in CONFIGURATION["osc"]["ports"].items():
    if CONFIGURATION["editor"]["greeter"]:
        logging.info(f"OSC Port added: {osc_port_name}")
        print(f"[bold yellow]> OSC Port added: [red]{osc_port_name}[/red] [/bold yellow]")
    globals()[osc_port_name] = OSC(
        name=osc_port_name, host=port["host"], port=port["port"], clock=clock
    )
    env.subscribe(globals()[osc_port_name])

c = clock
stop = clock.remove


def exit():
    """Exit the interactive shell"""
    clock._stop()


clock._start()

# == TEST AREA FOR THE PATTERN SYSTEM ======================================================

# if globals().get("superdirt", None) is not None:
#     superdirt = globals()["superdirt"]

#     @alias_param("sound", "s")
#     @alias_param("period", "p")
#     def dirt(*args, **kwargs):
#         """Example use:

#         >> aa * d(sound="bd", speed=2, amp=4)

#         >> aa * None
#         >> aa.stop()
#         """
#         # Manipulate to interpret the first args as "sound"
#         if not "sound" in kwargs:
#             kwargs["sound"] = args[0]

#         # Manipulate to replicate how "loopAt" works
#         if "loop" in kwargs:
#             loop = kwargs.pop("loop")
#             kwargs["unit"] = "c"
#             kwargs["speed"] = loop * (clock.tempo / clock._denominator) / 60
#             kwargs["cut"] = 1
#         return Player._play_factory(superdirt.player_dirt, *args, **kwargs)


# if globals().get("midi", None) is not None:
#     midi = globals()["midi"]

#     @alias_param("period", "p")
#     def debug(*args, **kwargs):
#         return Player._play_factory(pattern_printer, *args, **kwargs)

#     @alias_param("period", "p")
#     def tick(*args, **kwargs):
#         return Player._play_factory(midi.tick, *args, **kwargs)

#     @alias_param("length", "len")
#     @alias_param("channel", "chan")
#     @alias_param("velocity", "vel")
#     @alias_param("period", "p")
#     def note(*args, **kwargs):
#         return Player._play_factory(midi.note, *args, nudge=-0.15, **kwargs)

#     @alias_param("channel", "chan")
#     @alias_param("control", "ctrl")
#     @alias_param("value", "val")
#     @alias_param("period", "p")
#     def cc(*args, **kwargs):
#         return Player._play_factory(midi.control_change, *args, **kwargs)

#     @alias_param("channel", "chan")
#     @alias_param("program", "prg")
#     @alias_param("period", "p")
#     def pc(*args, **kwargs):
#         return Player._play_factory(midi.program_change, *args, **kwargs)

#     @alias_param("period", "p")
#     def bd(*args, **kwargs):
#         return Player._play_factory(midi.pitch_bend, *args, **kwargs)

#     @alias_param("period", "p")
#     def sy(*args, **kwargs):
#         return Player._play_factory(midi.sysex, *args, **kwargs)

#     if globals().get("kabelsalat_instrument", None) is not None:
#         kabel = globals()["kabelsalat_instrument"]

#         @alias_param("period", "p")
#         def kabelsalat(*args, **kwargs):
#             return Player._play_factory(kabel, *args, **kwargs)


# # Adding all patterns to the global scope
# patterns = Player.initialize_patterns(clock)
# for pattern in patterns.values():
#     env.subscribe(pattern)
# for key, value in patterns.items():
#     globals()[key] = value


# def silence(*args):
#     if len(args) == 0:
#         env.dispatch("main", "silence", {})
#         for key in patterns.keys():
#             globals()[key].stop()
#         if "graph" in globals():
#             graph.clear()
#     else:
#         for arg in args:
#             arg.stop()


# R = Rest

# == NEW PATTERN SYSTEM, LET'S TRY IT ======================================================

from .Systems.Carousel import *
from .Systems.Carousel import vortex_clock_callback

clock._vortex_clock_callback = vortex_clock_callback
