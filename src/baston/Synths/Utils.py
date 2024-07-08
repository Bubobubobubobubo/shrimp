from signalflow import AudioGraph


def _note_to_freq(note: int):
    """Note to frequency conversion method

    Args:
        note: A valid MIDI note (as integer)
    """
    return 440 * 2 ** ((int(note) - 69) / 12)


graph = AudioGraph()
