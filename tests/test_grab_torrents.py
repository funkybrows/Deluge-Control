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


def get_torrents_with(
    n_torrents, name_options=None, state_options=None, torrent_dt=None
):
    ret = {}
    if not torrent_dt or isinstance(torrent_dt, dt.datetime):
        use_dt = torrent_dt if torrent_dt else dt.datetime.utcnow()
        epoch = str(use_dt.timestamp()).encode("utf-8")
        torrent_dts = [epoch] * n_torrents
    elif isinstance(torrent_dt, (set, list, tuple)) and isinstance(
        torrent_dt[0], dt.datetime
    ):
        torrent_dts = torrent_dt
        torrent_dts = [
            str(torrent_dt.timestamp()).encode("utf-8") for torrent_dt in torrent_dts
        ]
    else:
        raise ValueError(
            f"torrent_dt ({torrent_dt}) must be None, dt, or iterable of dts"
        )

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
        torrent_info["time_added".encode("utf-8")] = torrent_dts[i]
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

    @staticmethod
    def test_grab_only_new_torrents(deluge_client, movie_names, db_session):
        deluge_client.decode_torrent_data(
            encoded_results := get_torrents_with(2, movie_names, ["Seeding"])
        )
        with mock.patch(
            "deluge_control.client.DelugeClient.get_torrents_status"
        ) as mock_torrents:
            mock_torrents.return_value = {
                (
                    encoded_torrent_id := tuple(encoded_results.keys())[0]
                ): encoded_results[encoded_torrent_id]
            }
            first_torrent = register_new_torrents(deluge_client, db_session)[0]

            mock_torrents.return_value = encoded_results
            new_torrents = register_new_torrents(deluge_client, db_session)
            assert len(new_torrents) == 1 and first_torrent not in new_torrents
