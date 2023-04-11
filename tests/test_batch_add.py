from pathlib import Path
from unittest import mock

import pytest
import tenacity
from deluge_client.client import RemoteException
from deluge_control.client import get_deluge_client


@pytest.fixture
def mock_add_torrent():
    with mock.patch(
        "deluge_control.client.DelugeClient.add_torrent_file_async"
    ) as mock_add_torrent:
        yield mock_add_torrent


@pytest.fixture
def one_file_test_dir():
    (test_dir := Path("tests/one_file_test")).mkdir(exist_ok=True)
    Path(test_dir, "alice.torrent").hardlink_to(Path("tests/data/alice.torrent"))
    yield test_dir
    for file in test_dir.iterdir():
        file.unlink()
    test_dir.rmdir()


def test_one_file(mock_add_torrent, one_file_test_dir):
    deluge_client = get_deluge_client()
    deluge_client.batch_add_torrents(one_file_test_dir)
    mock_add_torrent.assert_called_once()


def test_multiple_files(mock_add_torrent):
    assert Path("tests/data/").exists()
    (test_dir := Path("tests/multi_file_test")).mkdir(exist_ok=True)
    for file_or_folder in Path("tests/data").iterdir():
        if file_or_folder.is_file() and file_or_folder.suffix == ".torrent":
            Path(test_dir, file_or_folder.name).hardlink_to(file_or_folder)

    try:
        deluge_client = get_deluge_client()
        deluge_client.batch_add_torrents(test_dir)
        for file in test_dir.iterdir():
            mock_add_torrent.assert_any_call(
                file.stem, file_dump=file.read_bytes(), add_paused=True
            )
    finally:
        for file in test_dir.iterdir():
            file.unlink()
        test_dir.rmdir()


def test_file_already_present(mock_add_torrent, one_file_test_dir):
    deluge_client = get_deluge_client()
    mock_add_torrent.side_effect = RemoteException("Torrent already in session")
    with pytest.raises(tenacity.RetryError):
        deluge_client.batch_add_torrents(one_file_test_dir, retries=2, wait_duration=1)
