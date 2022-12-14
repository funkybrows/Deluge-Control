import datetime as dt
import random
from sqlalchemy.sql.expression import select
from deluge_control.models import StateChoices, Torrent, TorrentSnapshot
from deluge_control.check_torrents import check_seeding_torrents
from deluge_control.register_torrents import register_new_torrents
from utils import get_torrents_with, patch_torrents_status, encode_torrent_data


def get_check_torrents_info(torrent_ids, state_options):
    return encode_torrent_data(
        {
            torrent_id: {
                "total_uploaded": random.randint(1 * 1024**2, 1 * 1024**3),
                "total_seeds": random.randint(0, 500),
                "total_peers": random.randint(0, 500),
                "state": random.choice(state_options),
            }
            for torrent_id in torrent_ids
        }
    )


def test_check_torrent(deluge_client, movie_names, db_5_sessions):
    with patch_torrents_status() as mock_torrents:
        mock_torrents.return_value = get_torrents_with(1, movie_names[1], ("Seeding",))
        register_new_torrents(deluge_client, db_5_sessions[0])
        torrent = db_5_sessions[1].execute(select(Torrent)).scalars().all()[0]
        assert not db_5_sessions[1].execute(select(TorrentSnapshot)).scalars().all()
        mock_torrents.return_value = get_check_torrents_info(
            (torrent.torrent_id,), ("Seeding",)
        )
        checked_torrents = check_seeding_torrents(deluge_client, db_5_sessions[2])
        assert (expected_id := checked_torrents[0].torrent.torrent_id) in (
            db_returned_ids := [
                row.torrent_id
                for row in db_5_sessions[3]
                .execute(
                    select(Torrent.torrent_id)
                    .select_from(TorrentSnapshot)
                    .join(TorrentSnapshot.torrent)
                    .where(TorrentSnapshot.torrent == torrent)
                )
                .all()
            ]
        ), f"expected_id: {expected_id}, not in {db_returned_ids}"
        assert checked_torrents[0].torrent.next_check_time > dt.datetime.utcnow()


def test_change_seeding_to_paused(deluge_client, movie_names, db_5_sessions):
    with patch_torrents_status() as mock_torrents:
        mock_torrents.return_value = get_torrents_with(1, movie_names[:1], ("Seeding",))
        register_new_torrents(deluge_client, db_5_sessions[0])
        torrent_name, torrent_state = (
            db_5_sessions[1].execute(select(Torrent.name, Torrent.state)).all()[0]
        )
        assert torrent_name and torrent_state == StateChoices.SEED
        mock_torrents.return_value = get_check_torrents_info(
            deluge_client.decode_torrent_data(mock_torrents.return_value).keys(),
            ("Paused",),
        )
        check_seeding_torrents(deluge_client, db_5_sessions[2])
        torrent = db_5_sessions[3].execute(select(Torrent)).scalars().first()
        assert torrent.state == StateChoices.PAUSE and torrent.name == torrent_name


def test_change_seeding_to_deleted(deluge_client, movie_names, db_5_sessions):
    with patch_torrents_status() as mock_torrents:
        mock_torrents.return_value = get_torrents_with(1, movie_names[:1], ("Seeding",))
        register_new_torrents(deluge_client, db_5_sessions[0])
        torrent_name, torrent_state = (
            db_5_sessions[1].execute(select(Torrent.name, Torrent.state)).all()[0]
        )
        assert torrent_name and torrent_state == StateChoices.SEED
        mock_torrents.return_value = {}
        check_seeding_torrents(deluge_client, db_5_sessions[2])
        torrent = db_5_sessions[3].execute(select(Torrent)).scalars().first()
        assert torrent.state == StateChoices.DEL and torrent.name == torrent_name
