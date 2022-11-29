from pathlib import Path
from os import path
import logging.config

log_file_path = path.join(
    Path(__file__).parent.parent.absolute(), "config", "logging.conf"
)
logging.config.fileConfig(log_file_path)
