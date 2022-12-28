from unittest import mock

from deluge_control.models import StateChoices


def get_torrents_by_id(n_torrents):
    random_list = [chr(num) for num in (range(ord("a"), ord("z") + 1))] + [
        str(num) for num in range(0, 10)
    ]

    return {
        "".join(random.choice(random_list) for _ in range(50)): []
        for _ in range(n_torrents)
    }


import datetime as dt
import random


def encode_torrent_data(torrent_data_dict):
    ret = {}
    for torrent_id, torrent_data in torrent_data_dict.items():
        ret[torrent_id.encode("utf-8")] = (encoded_data_dict := {})
        for key, value in torrent_data.items():
            encoded_data_dict[key.encode("utf-8")] = (
                value.encode("utf-8") if isinstance(value, str) else value
            )
    return ret


def get_torrents_with(
    n_torrents, name_options=None, state_options=None, torrent_dt=None
):
    ret = {}
    if not torrent_dt or isinstance(torrent_dt, dt.datetime):
        use_dt = torrent_dt if torrent_dt else dt.datetime.utcnow()
        epoch = use_dt.timestamp()
        torrent_dts = [epoch] * n_torrents
    elif isinstance(torrent_dt, (set, list, tuple)) and isinstance(
        torrent_dt[0], dt.datetime
    ):
        torrent_dts = torrent_dt
        torrent_dts = [torrent_dt.timestamp() for torrent_dt in torrent_dts]
    else:
        raise ValueError(
            f"torrent_dt ({torrent_dt}) must be None, dt, or iterable of dts"
        )

    if name_options:
        name_options = random.sample(name_options, n_torrents)
    for i, torrent_id in enumerate(get_torrents_by_id(n_torrents)):
        ret[torrent_id] = (torrent_info := {})
        torrent_info["state"] = random.choice(
            (
                state_options
                or state_options
                or [member.value for member in list(StateChoices)]
            )
        )
        if name_options:
            torrent_info["name"] = name_options[i]
        torrent_info["time_added"] = torrent_dts[i]
    return encode_torrent_data(ret)


def patch_torrents_status():
    return mock.patch("deluge_control.client.DelugeClient.get_torrents_status")
