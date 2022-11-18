import base64
import pytest

import os
import os.path

from deluge_control.client import DelugeClient

@pytest.fixture(scope="session")
def deluge_client():
    return DelugeClient()

def test_add_torrent(deluge_client):
    torrent_id = deluge_client.add_torrent_file_async('alice', 'tests/data/alice.torrent', download_location=cfg['tests.root_dir'], move_completed=False)
    try:
        assert torrent_id
    finally:
        deluge_client.remove_torrent(torrent_id, remove_data=False)


