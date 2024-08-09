import logging
import json
import os
import appdirs
import pathlib
import mido
import sys

APPNAME = "Shrimp"
APPAUTHOR = "Raphaël Forment"
USER_DIRECTORY = appdirs.user_data_dir(APPNAME, APPAUTHOR)
LOG_FILE = os.path.join(USER_DIRECTORY, "shrimp.log")


def _ensure_log_file_exists():
    """Ensure that the log file exists."""
    try:
        if not os.path.exists(USER_DIRECTORY):
            os.makedirs(USER_DIRECTORY)
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "a") as f:
                pass
    except OSError as e:
        print(f"An error occurred while ensuring the log file exists: {e}")


_ensure_log_file_exists()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s  [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    filename=os.path.join(USER_DIRECTORY, "shrimp.log"),
    filemode="w",
)


def _find_default_output_midi_port() -> str:
    """Find the default MIDI port to use by default when config is created."""
    if sys.platform in "win32":
        port_list = mido.get_output_names()
        if port_list:
            return port_list[0]
        else:
            return False
    else:
        return "shrimp"


def _find_default_input_midi_port() -> str:
    """Find the default MIDI port to use by default when config is created."""
    if sys.platform in "win32":
        port_list = mido.get_input_names()
        if port_list:
            return port_list[0]
        else:
            return False
    else:
        return "shrimp"


def open_config_folder():
    """Cross-platform function to open the configuration folder in the file explorer."""
    try:
        os.startfile(USER_DIRECTORY)
    except AttributeError:
        import subprocess
        import sys

        if sys.platform.startswith("darwin"):
            subprocess.call(["open", USER_DIRECTORY])
        elif sys.platform.startswith("linux"):
            subprocess.call(["xdg-open", USER_DIRECTORY])
        elif sys.platform.startswith("win"):
            subprocess.call(["explorer", USER_DIRECTORY])


def _create_default_configuration() -> dict:
    """Create a default configuration for Shrimp."""
    configuration = {
        "clock": {
            "default_tempo": 135,
            "time_grain": 0.01,
            "delay": 0,
        },
        "midi": {
            "out_ports": [
                {"midi": _find_default_output_midi_port(), "instruments": [], "controllers": []}
            ],
            "in_ports": {
                "midi_in": _find_default_input_midi_port(),
            },
        },
        "osc": {
            "ports": {
                "superdirt": {
                    "host": "127.0.0.1",
                    "port": 57120,
                    "name": "SuperDirt",
                },
            }
        },
        "editor": {
            "default_shell": "ptpython",
            "vim_mode": False,
            "print_above": False,
            "greeter": True,
        },
        "audio_engine": {
            "enabled": False,
            "sample_rate": 44100,
            "cpu_limit": 50,
            "output_buffer_size": 256,
            "input_buffer_size": 256,
            "output_backend_name": "auto",
        },
    }
    return configuration


def _check_for_configuration() -> None:
    """Make sure the configuration file/dir exists. If not, create it."""
    try:
        if not os.path.exists(USER_DIRECTORY):
            os.makedirs(USER_DIRECTORY)
            logging.debug(f"Created user directory at {USER_DIRECTORY}")
    except OSError as e:
        logging.error(f"An error occurred while creating the user directory: {e}")

    config_path = os.path.join(USER_DIRECTORY, "config.json")

    try:
        if not os.path.exists(config_path) or os.path.getsize(config_path) == 0:
            file = _create_default_configuration()
            with open(config_path, "w") as f:
                json.dump(file, f, indent=4)
            logging.debug(f"Created configuration file with default settings at {config_path}")
    except OSError as e:
        logging.error(f"An error occurred while creating the configuration file: {e}")

    def _update_configuration(config: dict, template: dict) -> dict:
        """Recursively update the configuration dictionary with missing keys from the template."""
        for key in template:
            if key not in config:
                config[key] = template[key]
            elif isinstance(config[key], dict) and isinstance(template[key], dict):
                config[key] = _update_configuration(config[key], template[key])
        return config

    # Check if the configuration file has all the required keys also present in the template
    try:
        with open(config_path, "r") as f:
            content = json.load(f)
            template = _create_default_configuration()
            content = _update_configuration(content, template)
            with open(config_path, "w") as f:
                json.dump(content, f, indent=4)
    except OSError as e:
        logging.error(f"An error occurred while updating the configuration file: {e}")


def read_configuration() -> dict:
    """Read the configuration file for Shrimp."""
    _check_for_configuration()
    config_path = os.path.join(USER_DIRECTORY, "config.json")

    try:
        with open(config_path, "r") as f:
            content = f.read()
            return json.loads(content)
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from the configuration file: {e}")
        return _create_default_configuration()


def write_configuration(configuration: dict):
    """Write the configuration to the configuration file."""
    _check_for_configuration()
    config_path = os.path.join(USER_DIRECTORY, "config.json")

    try:
        with open(config_path, "w") as f:
            json.dump(configuration, f, indent=4)
        logging.debug(f"Wrote configuration to {config_path}")
    except OSError as e:
        logging.error(f"An error occurred while writing to the configuration file: {e}")


def get_ptpython_history_file() -> str:
    """
    Retrieve the path to the ptpython history file, ensuring the directory and file exist.

    Returns:
        str: Path to the history file.
    """

    # Ensure the directory exists
    pathlib.Path(USER_DIRECTORY).mkdir(parents=True, exist_ok=True)

    # Path to the history file
    history_file = os.path.join(USER_DIRECTORY, "history")

    # Ensure the history file exists
    if not os.path.exists(history_file):
        with open(history_file, "a"):
            os.utime(history_file, None)

    return history_file
