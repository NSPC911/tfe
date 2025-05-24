"""Module that holds variable states + other functions"""

import base64
from toml import loads, dumps
from os import path
from time import sleep
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import re
from threading import Thread


def log(*object):
    with open(
        path.join(path.dirname(__file__), "log.txt"),
        "+a",
    ) as logger:
        logger.write(f"{' '.join(object) if type(object) is list else object}\n")


sessionDirectories = []
sessionHistoryIndex = 0
sessionLastHighlighted = {}
config = {}
"""
def log(string):
    with open(
        path.join(path.dirname(__file__), "log.txt"),
        "+a",
    ) as logger:
        logger.write(f"{string}\n")
"""


def get_nested_value(dictionary, keys_list):
    """
    Get a value from a nested dictionary using a list of keys.

    Args:
        dictionary (dict): The dictionary to traverse
        keys_list (list): List of keys to navigate the dictionary
        default: Value to return if the path doesn't exist (default: None)

    Returns:
        The value at the specified path or default if not found
    """
    current = dictionary

    try:
        for key in keys_list:
            current = current[key]
        return current
    except (KeyError, TypeError):
        return None


def update_session_state(directories, index, lastHighlighted={}) -> None:
    """
    Update the session state with the given directories and index.

    Args:
        directories (list): List of directories in the session.
        index (int): Current index in the session history.
        lastHighlighted (str): The last highlighted file or directory.
    """
    global sessionDirectories
    global sessionHistoryIndex
    global sessionLastHighlighted
    sessionDirectories = directories
    sessionHistoryIndex = index
    sessionLastHighlighted = lastHighlighted


def load_config() -> None:
    """
    Load the configuration from a TOML file.

    Args:
        config_path (str): Path to the configuration file.
    """

    global config
    with open(path.join(path.dirname(__file__), "config/config.toml"), "r") as f:
        config = loads(f.read())
    log(config)
    # update styles
    # get vars to replace
    with open(path.join(path.dirname(__file__), "config/template_style.tcss"), "r") as f:
        template = f.read()
    # replace vars with values from config
    vars = r"\$\-([^\$]+)-\$"
    for match in re.findall(vars, template):
        match_keys = match.split("-")
        log(match_keys)
        config_value = get_nested_value(config, match_keys)
        if config_value is not None:
            template = template.replace(f"$-{match}-$", str(config_value))
    with open(path.join(path.dirname(__file__), "style.tcss"), "w") as f:
        f.write(template)


class FileEventHandler(FileSystemEventHandler):
    @staticmethod
    def on_modified(event):
        if event.is_directory:
            return
        elif path.basename(event.src_path) in ["config.toml", "template_style.tcss"]:
            log(f"File modified: {event.src_path}")
            load_config()


def watch_config_file() -> None:
    event_handler = FileEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path=path.dirname(__file__), recursive=False)
    observer.start()
    log("Watching for changes in config.toml and template_style.tcss")
    try:
        while True:
            sleep(1)
    except:
        observer.stop()
    observer.join()


Thread(
    target=watch_config_file,
    daemon=True,
).start()

def encode_base64(text: str) -> str:
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')

def decode_base64(text: str) -> str:
    return base64.b64decode(text.encode('utf-8')).decode('utf-8')