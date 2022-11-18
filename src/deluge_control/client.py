import base64
from sonarr_announced import deluge

import os
import os.path

class DelugeClient():
    POSSIBLE_ADD_OPTIONS = {
        "download_location",
        "move_completed"
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
    def __init__(self):
        self.client = deluge.get_deluge_client()
    
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

    def add_torrent_file_async(self, name, file_path, **options):
        with open(file_path, 'rb') as f:
            content = f.read()
        encoded_content = base64.b64encode(content)

        add_options = self.get_approved_keys_dict(options, self.POSSIBLE_ADD_OPTIONS) if options else {}
        return self.client.call('core.add_torrent_file_async', name, encoded_content, add_options)
    

        result = self.client.call('core.add_torrent_file_async', name, encoded_content, add_options)
        return result
    
    def remove_torrent(self, torrent_id, remove_data=False):
        return self.client.call('core.remove_torrent', torrent_id, remove_data=remove_data)

