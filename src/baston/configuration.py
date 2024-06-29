import logging
import json
import os
import appdirs

APPNAME = "Baston"
APPAUTHOR = "Raphaël Forment"
USER_DIRECTORY = appdirs.user_data_dir(APPNAME, APPAUTHOR)


def _create_default_configuration() -> dict:
    """Create a default configuration for Baston."""
    configuration = {
        "tempo": 120,
        "midi_out_port": "MIDI Bus 1",
        "midi_in_port": "MIDI Bus 1",
        "default_shell": "python",
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

    # Check if the configuration file has all the required keys also present in the template
    try:
        with open(config_path, "r") as f:
            content = json.load(f)
            template = _create_default_configuration()
            for key in template:
                if key not in content:
                    content[key] = template[key]
            with open(config_path, "w") as f:
                json.dump(content, f, indent=4)
    except OSError as e:
        logging.error(f"An error occurred while updating the configuration file: {e}")


def read_configuration() -> dict:
    """Read the configuration file for Baston."""
    _check_for_configuration()
    config_path = os.path.join(USER_DIRECTORY, "config.json")

    try:
        with open(config_path, "r") as f:
            content = f.read()
            logging.debug(f"Configuration file content: {content}")
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
