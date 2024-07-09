from signalflow import AudioGraph, AudioGraphConfig
from ..configuration import read_configuration
from typing import Literal

CONFIG = read_configuration()


def _note_to_freq(note: int):
    """Note to frequency conversion method

    Args:
        note: A valid MIDI note (as integer)
    """
    return 440 * 2 ** ((int(note) - 69) / 12)


def create_new_audio_graph(
    sample_rate: int = 44100,
    cpu_limit: int = 50,
    output_buffer_size: int = 256,
    input_buffer_size: int = 256,
    output_backend_name: Literal[
        "jack", "alsa", "pulseaudio", "coreaudio", "wasapi", "dummy"
    ] = "auto",
):
    """Create a new SignalFlow AudioGraph instance with custom parameters.

    Args:
        sample_rate (int): The sample rate of the audio graph
        cpu_limit (int): The CPU usage limit of the audio graph
        output_buffer_size (int): The output buffer size of the audio graph
        input_buffer_size (int): The input buffer size of the audio graph
        output_backend_name (str): The output backend name of the audio graph

    Returns:
        AudioGraph: A new AudioGraph
    """
    graph_config = AudioGraphConfig()
    graph_config.sample_rate = sample_rate
    graph_config.output_buffer_size = output_buffer_size
    graph_config.input_buffer_size = input_buffer_size
    graph_config.cpu_usage_limit = max(0, min(cpu_limit, 100)) / 100
    if output_backend_name != "auto":
        graph_config.output_backend_name = output_backend_name
    return AudioGraph(graph_config)


graph = create_new_audio_graph(
    sample_rate=CONFIG["audio_engine"]["sample_rate"],
    cpu_limit=CONFIG["audio_engine"]["cpu_limit"],
    output_buffer_size=CONFIG["audio_engine"]["output_buffer_size"],
    input_buffer_size=CONFIG["audio_engine"]["input_buffer_size"],
    output_backend_name=CONFIG["audio_engine"]["output_backend_name"],
)
