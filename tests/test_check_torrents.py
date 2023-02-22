import datetime as dt
import random
from sqlalchemy.sql.expression import select
    split_ready_db_torrents_by_state,
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


def test_split_torrents_only_covers_ready_torrents(movie_names, db_5_sessions):
    iter_sessions = iter(db_5_sessions)
    with next(iter_sessions) as db_session:
        normal_torrent = Torrent(
            torrent_id=(normal_torrent_id := "abcd1234"),
            name=movie_names[0],
            time_added=(now := dt.datetime.utcnow()),
            state=StateChoices.SEED,
        )
        db_session.add(normal_torrent)
        delayed_torrent = Torrent(
            torrent_id=(delayed_torrent_id := "abcd4321"),
            name=movie_names[2],
            time_added=now,
            next_check_time=now + dt.timedelta(days=1),
            state=StateChoices.SEED,
        )
        db_session.add(delayed_torrent)
        db_session.commit()

    with next(iter_sessions) as db_session:
        ready_db_torrents = split_ready_db_torrents_by_state(db_session)[
            StateChoices.SEED
        ]
        assert delayed_torrent_id not in ready_db_torrents
        assert normal_torrent_id in ready_db_torrents


def test_split_torrents_by_state(deluge_client, movie_names, db_5_sessions):
    iter_sessions = iter(db_5_sessions)
    with patch_torrents_status() as mock_torrents:
        mock_torrents.return_value = {
            **get_torrents_with(2, movie_names[0:2], ("Downloading",)),
            **get_torrents_with(2, movie_names[2:], ("Seeding",)),
        }
        register_new_torrents(deluge_client, next(iter_sessions))
        torrents = next(iter_sessions).execute(select(Torrent)).scalars().all()
        torrents_by_state = split_ready_db_torrents_by_state(next(iter_sessions))

        for torrent in torrents:
            assert isinstance(
                torrents_by_state[torrent.state][torrent.torrent_id], Torrent
            )

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
