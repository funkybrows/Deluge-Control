import datetime as dt
import random
from unittest import mock
from faker import Faker

from deluge_control.models import StateChoices
from deluge_control.register_torrents import Torrent, register_new_torrents

from utils import get_torrents_with, patch_torrents_status


class TestGrabNewTorrents:
    @staticmethod
    def test_single_new_torrent(deluge_client, movie_names, db_session):
        with patch_torrents_status() as mock_torrents:
            mock_torrents.return_value = get_torrents_with(1, movie_names, ["Seeding"])
            new_torrents = register_new_torrents(deluge_client, db_session)
        decoded_mocked_value = deluge_client.decode_torrent_data(
            mock_torrents.return_value
        )
        mock_torrent_id = list(decoded_mocked_value.keys())[0]
        assert (new_torrent := new_torrents[0]).torrent_id == (
            decoded_mock_torrent_id := mock_torrent_id
        ), f"{new_torrent.torrent_id} != {decoded_mock_torrent_id}"
        assert new_torrent.name == (
            decoded_mock_torrent_name := decoded_mocked_value[mock_torrent_id]["name"]
        ), f"{new_torrent.name} != {decoded_mock_torrent_name}"
        assert new_torrent.state == StateChoices.SEED

    @staticmethod
    def test_grab_only_new_torrents(deluge_client, movie_names, db_session):
        deluge_client.decode_torrent_data(
            encoded_results := get_torrents_with(
                2,
                movie_names,
                ("Seeding",),
                torrent_dt=(
                    (now := dt.datetime.utcnow()),
                    now + dt.timedelta(minutes=1),
                ),
            )
        )
        with patch_torrents_status() as mock_torrents:
            mock_torrents.return_value = {
                (
                    encoded_torrent_id := tuple(encoded_results.keys())[0]
                ): encoded_results[encoded_torrent_id]
            }
            first_torrent = register_new_torrents(deluge_client, db_session)[0]

            mock_torrents.return_value = encoded_results
            new_torrents = register_new_torrents(deluge_client, db_session)
            assert len(new_torrents) == 1 and first_torrent not in new_torrents

    @staticmethod
    def test_torrent_dt_saved_correctly(deluge_client, movie_names, db_session):
        now = dt.datetime.utcnow()
        deluge_client.decode_torrent_data(
            encoded_results := get_torrents_with(
                1,
                movie_names,
                ("Seeding",),
                torrent_dt=(now,),
            )
        )
        with patch_torrents_status() as mock_torrents:
            mock_torrents.return_value = {
                (
                    encoded_torrent_id := tuple(encoded_results.keys())[0]
                ): encoded_results[encoded_torrent_id]
            }
            first_torrent = register_new_torrents(deluge_client, db_session)[0]
            assert first_torrent.time_added == now
