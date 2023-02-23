import pytest

import os
import os.path


TESTS_ROOT_DIR = os.environ.get("DELUGE_REMOTE_TESTS_ROOT_DIR")


@pytest.fixture
def inferno_torrent(deluge_client):
    if os.path.exists("tests/data/inferno.txt"):
        with open("tests/data/inferno.txt") as f:
            return f.read()
    else:
        torrent_id = deluge_client.add_torrent_file_async(
            "inferno",
            "tests/data/inferno.torrent",
            download_location=TESTS_ROOT_DIR,
            move_completed=False,
        )

        with open("tests/data/inferno.txt", "w") as write_f:
            write_f.write(torrent_id.decode("utf-8"))
        return torrent_id


def test_add_torrent(deluge_client):
    torrent_id = deluge_client.add_torrent_file_async(
        "alice",
        "tests/data/alice.torrent",
        download_location=TESTS_ROOT_DIR,
        move_completed=False,
    )
    try:
        assert torrent_id
    finally:
        deluge_client.remove_torrent(torrent_id, remove_data=False)


def test_get_torrent_status(inferno_torrent, deluge_client):
    result = deluge_client.get_torrent_status(inferno_torrent, ["name", "state"])
    decoded_result = {
        key.decode("utf-8"): value.decode("utf-8") for key, value in result.items()
    }
    assert decoded_result["name"] == "inferno00dant_2"
    assert decoded_result["state"] in ("Seeding", "Downloading", "Error")
