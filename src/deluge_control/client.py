import base64
from sonarr_announced import deluge

import os
import os.path

class DelugeClient():
    POSSIBLE_ADD_OPTIONS = {
        "download_location",
        "move_completed"
    }
    def __init__(self):
        self.client = deluge.get_deluge_client()
    
    def add_torrent_file_async(self, name, file_path, **options):
        with open(file_path, 'rb') as f:
            content = f.read()
        encoded_content = base64.b64encode(content)

        add_options = {}
        if options:
            for possible_add_option in self.POSSIBLE_ADD_OPTIONS:
                if option_value:= options.get(possible_add_option):
                    add_options[possible_add_option] = option_value

        result = self.client.call('core.add_torrent_file_async', name, encoded_content, add_options)
        return result
    
    def remove_torrent(self, torrent_id, remove_data=False):
        self.client.call('core.remove_torrent', torrent_id, remove_data=remove_data)

