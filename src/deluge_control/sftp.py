import logging
import os

import pysftp

logger = logging.getLogger("deluge.sftp")


def get_sftp_connection(
    hostname=os.environ.get("REMOTE_SFTP_HOST"),
    username=os.environ.get("REMOTE_SFTP_USER"),
    private_key=f"{os.environ.get('CONFIG_FOLDER_PATH')}/.ssh/id_rsa",
    known_hosts=f"{os.environ.get('CONFIG_FOLDER_PATH')}/.ssh/known_hosts",
):
    logger.debug(
        "Making sftp connection to %s@%s. Priv key file: %s, Known hosts file: %s",
        username,
        hostname,
        private_key,
        known_hosts,
    )
    connection_options = pysftp.CnOpts(knownhosts=known_hosts)
    return pysftp.Connection(
        hostname, username=username, private_key=private_key, cnopts=connection_options
    )
