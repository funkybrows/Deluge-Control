import random
from unittest import mock
from faker import Faker

from deluge_control.models import StateChoices
from deluge_control.torrents import Torrent, register_new_torrents


random_list = [chr(num) for num in (range(ord("a"), ord("z") + 1))] + [
    str(num) for num in range(0, 10)
]


def get_torrents_by_id(n_torrents):
    return {
        "".join(random.choice(random_list) for _ in range(50)).encode("utf-8"): []
        for _ in range(n_torrents)
    }


def get_torrents_with(n_torrents, name_options=None, state_options=None):
    ret = {}
    if name_options:
        name_options = random.sample(name_options, n_torrents)
    for i, torrent_id in enumerate(get_torrents_by_id(n_torrents)):
        ret[torrent_id] = (torrent_info := {})
        if state_options:
            torrent_info["state".encode("utf-8")] = random.choice(state_options).encode(
                "utf-8"
            )
        if name_options:
            torrent_info["name".encode("utf-8")] = name_options[i].encode("utf-8")
    return ret


class TestGrabNewTorrents:
    @staticmethod
    def test_single_new_torrent(deluge_client, movie_names, db_session):
        with mock.patch(
            "deluge_control.client.DelugeClient.get_torrents_status"
        ) as mock_torrents:

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

    # @staticmethod
    # def test_grab_only_new_torrents(deluge_client, movie_names, db_session):
    #     full_results = deluge_client.decode_data(
    #         get_torrents_with(2, movie_names, ["Seeding"])
    #     )


# b'3270966a95ccf1a72493e4948e826508906a5a34': {b'name': b'Star Wars Andor (2022) S01E03 (2160p DSNP WEB-DL x265 HEVC 10bit DDP 5.1 Vyndros)'}
