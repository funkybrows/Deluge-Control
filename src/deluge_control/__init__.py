import logging.config

from deluge_control import utils

logging.config.fileConfig(
    f"{utils.get_config_folder_path()}/logging.conf",
    defaults={"log_folder_path": utils.get_log_folder_path()},
)
