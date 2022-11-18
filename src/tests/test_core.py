import base64
import pytest

import os
import os.path

from deluge_control import config
from deluge_control.client import DelugeClient

cfg = config.init()

@pytest.fixture(scope="session")
def deluge_client():
    return DelugeClient()

@pytest.fixture
def inferno_torrent(deluge_client):
    if os.path.exists('tests/data/inferno.txt'):
        with open('tests/data/inferno.txt') as f:
            return f.read()
    else:
            torrent_id = deluge_client.add_torrent_file_async('inferno', 'tests/data/inferno.torrent', download_location=cfg['tests.root_dir'], move_completed=False)

            with open('tests/data/inferno.txt', 'w') as write_f:
                write_f.write(torrent_id.decode('utf-8'))
            return torrent_id

def test_add_torrent(deluge_client):
    torrent_id = deluge_client.add_torrent_file_async('alice', 'tests/data/alice.torrent', download_location=cfg['tests.root_dir'], move_completed=False)
    try:
        assert torrent_id
    finally:
        deluge_client.remove_torrent(torrent_id, remove_data=False)


def test_get_torrent_status(inferno_torrent, deluge_client):
    result = deluge_client.call('core.get_torrent_status', inferno_torrent, ['name', 'state'])
    assert {key.decode('utf-8'): value.decode('utf-8') for key, value in result.items()} == {'name': 'inferno00dant_2', 'state': 'Seeding'}
