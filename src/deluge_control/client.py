import asyncio
import base64
import logging
import os
import os.path
from typing import Any, Dict, List

from deluge_client import DelugeRPCClient

logger = logging.getLogger("deluge.client")

DELUGE_CLIENT = None


def get_deluge_client():
    global DELUGE_CLIENT
    if not DELUGE_CLIENT:
        DELUGE_CLIENT = DelugeClient()
    return DELUGE_CLIENT


class DelugeClient:
    POSSIBLE_ADD_OPTIONS = {
        "download_location",
        "move_completed",
        "add_in_paused_state",
    }

    POSSIBLE_STATUS_KEYS = {
        "completed_time",
        "distributed_copies",
        "download_location",
        "download_payload_rate",
        "eta",
        "is_auto_managed",
        "last_seen_complete",
        "max_download_speed",
        "max_upload_speed",
        "name",
        "num_peers",
        "num_seeds",
        "progress",
        "queue",
        "ratio",
        "seeds_peers_ratio",
        "state",
        "time_added",
        "time_since_transfer",
        "total_done",
        "total_peers",
        "total_remaining",
        "total_seeds",
        "total_uploaded",
        "total_wanted",
        "tracker_host",
        "upload_payload_rate",
    }

    def __init__(self, host=None, port=None, username=None, password=None):
        self.client = DelugeRPCClient(
            host or os.environ.get("DEFAULT_DELUGE_HOST"),
            int(port or os.environ.get("DEFAULT_DELUGE_PORT")),
            username or os.environ.get("DEFAULT_DELUGE_USERNAME"),
            password or os.environ.get("DEFAULT_DELUGE_PASSWORD"),
        )

    async def connect_with_retry(self):
        while not self.client.connected:
            logger.debug("ATTEMPTING TO CONNECT TO CLIENT")
            try:
                self.client.connect()
                logger.debug("CONNECTED TO CLIENT")
            except Exception:
                logger.exception("Failed to connect to deluge client")
            await asyncio.sleep(1)

    @classmethod
    def decode_torrent_data(cls, deluge_data):
        if isinstance(deluge_data, dict):
            ret = {
                cls.decode_torrent_data(key): cls.decode_torrent_data(value)
                for key, value in deluge_data.items()
            }

        elif isinstance(deluge_data, list):
            value = [cls.decode_torrent_data(val) for val in value]

        elif isinstance(deluge_data, bytes):
            ret = deluge_data.decode("utf-8")
        else:
            ret = deluge_data
        return ret

    @classmethod
    def get_approved_keys_dict(cls, keys, available):
        approved = {}
        for possible_key in keys:
            if possible_key in available:
                approved[possible_key] = keys.get(possible_key)
        return approved

    @classmethod
    def get_approved_keys_list(cls, keys, available):
        approved = []
        for possible_key in keys:
            if possible_key in available:
                approved.append(possible_key)
        return approved

    def add_torrent_file_async(self, name, file_path=None, file_dump=None, **options):
        if not file_path or file_dump:
            raise ValueError("Either file path or dump required")

        if file_path:
            with open(file_path, "rb") as f:
                content = f.read()
        else:
            content = file_dump
        encoded_content = base64.b64encode(content)

        add_options = (
            self.get_approved_keys_dict(options, self.POSSIBLE_ADD_OPTIONS)
            if options
            else {}
        )
        return self.client.call(
            "core.add_torrent_file_async", name, encoded_content, add_options
        )

    def add_torrent_url(self, file_url, **options):
        add_options = (
            self.get_approved_keys_dict(options, self.POSSIBLE_ADD_OPTIONS)
            if options
            else {}
        )

        return self.client.call("core.add_torrent_url", file_url, add_options)

    def force_reannounce(self, torrent_ids: List[str]):
        return self.client.call("core.force_reannounce", torrent_ids)

    def get_method_list(self):
        return self.client.call("daemon.get_method_list")

    def get_torrent_status(self, torrent_id, keys: List[str]):
        status_keys = (
            self.get_approved_keys_list(keys, self.POSSIBLE_STATUS_KEYS) if keys else []
        )
        return self.client.call("core.get_torrent_status", torrent_id, status_keys)

    def get_torrents_status(self, keys: List[str], **filters: Dict[str, Any]):
        status_keys = (
            self.get_approved_keys_list(keys, self.POSSIBLE_STATUS_KEYS) if keys else []
        )
        return self.client.call("core.get_torrents_status", filters, status_keys)

    def remove_torrent(self, torrent_id, remove_data=False):
        return self.client.call(
            "core.remove_torrent", torrent_id, remove_data=remove_data
        )
