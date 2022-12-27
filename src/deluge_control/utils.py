import os
import os.path

PROJECT_NAME = "deluge-control"


def get_config_folder_path():
    return os.environ.get(
        "CONFIG_FOLDER_PATH",
        f'{os.path.expanduser("~")}/.{os.environ.get("PROJECT_NAME", PROJECT_NAME)}/config',
    )


def get_log_folder_path():
    return os.environ.get(
        "LOG_FOLDER_PATH",
        f'{os.path.expanduser("~")}/.{os.environ.get("PROJECT_NAME", PROJECT_NAME)}/logs',
    )
