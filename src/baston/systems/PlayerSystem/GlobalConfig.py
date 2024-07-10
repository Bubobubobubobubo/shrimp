from .Scales import SCALES


class GlobalConfig:
    """
    Singleton class representing the global configuration.

    This class ensures that only one instance of the GlobalConfig class is created
    and provides access to global properties.

    Attributes:
        _instance (GlobalConfig): The singleton instance of the GlobalConfig class.
        scale (str): The current scale.
        root (int): The root note.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalConfig, cls).__new__(cls)
            cls._instance.scale = SCALES.minor
            cls._register = {}
            cls._root_note = 60
        return cls._instance

    @property
    def register(self):
        return self._instance._register

    @register.setter
    def register(self, value):
        self._instance._register = value

    @property
    def scale(self):
        return self._instance._scale

    @scale.setter
    def scale(self, value):
        self._instance._scale = value

    @property
    def root(self):
        return self._instance._root_note

    @root.setter
    def root(self, value):
        self._instance._root_note = value


global_config = GlobalConfig()
