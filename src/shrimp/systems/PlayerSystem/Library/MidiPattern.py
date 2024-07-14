from ..Pattern import Pattern


class Pcc(Pattern):
    """Convenience function for reading incoming control changes
    on the given interface.

    Args:
        port (int): The MIDIIn object.
        channel (int): The channel number.
        control (int): The control number.

    Returns:
        int: The control change value.
    """

    def __init__(self, port: str, channel: int, control: int, default_value: int = 60):
        self._interface = port
        self._channel = channel
        self._control = control
        self._default_value = default_value

    def __call__(self, _):
        return self._interface.cc(self._channel, self._control, self._default_value)
