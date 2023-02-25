import datetime as dt
import random
import pytest
from sqlalchemy.sql.expression import select
from deluge_control.check_torrents import (
    check_seeding_torrents,
    split_ready_db_torrents_by_state,
)
from deluge_control.models import StateChoices, Torrent, TorrentXSeed
from utils import (
    get_seeding_torrents_info,
    patch_torrents_status,
    TORRENTS_STATUS_DEFAULT_ARGS,
)


def get_x_seed_query(torrent_id):
    return (
        select(TorrentXSeed)
        .join(Torrent.xseeds)
        .where(Torrent.torrent_id == torrent_id)
    )


@pytest.fixture
def seeding_torrent(movie_names):
    torrent_id = "abcd1234"
    return Torrent(
        torrent_id=torrent_id, name=random.choice(movie_names), state=StateChoices.SEED
    )


def test_generate_xseed(deluge_client, db_5_sessions, seeding_torrent):
    """
    If one doesn't exist, we should generate an xseed obj for a seeding
    torrent.
    """
    iter_sessions = iter(db_5_sessions)
    with next(iter_sessions) as db_session:
        db_session.add(seeding_torrent)
        db_session.commit()

    with patch_torrents_status() as mock_status:
        with next(iter_sessions) as db_session:
            db_session.add(seeding_torrent)
            mock_status.return_value = get_seeding_torrents_info(
                (seeding_torrent.torrent_id,)
            )
            assert not (
                db_session.execute(get_x_seed_query(seeding_torrent.torrent_id))
                .scalars()
                .first()
            )
            db_seeding_torrents = split_ready_db_torrents_by_state(db_session)[
                StateChoices.SEED
            ]
            client_torrents = deluge_client.decode_torrent_data(
                deluge_client.get_torrents_status(*TORRENTS_STATUS_DEFAULT_ARGS)
            )
            check_seeding_torrents(db_session, db_seeding_torrents, client_torrents)
            assert (
                db_session.execute(get_x_seed_query(seeding_torrent.torrent_id))
                .scalars()
                .first()
            )


def test_xseed_checks_updated_on_creation(
    deluge_client, db_5_sessions, seeding_torrent
):
    """
    On creation, xseed.next_check and last_check should both be set
    """
    iter_sessions = iter(db_5_sessions)
    with next(iter_sessions) as db_session:
        db_session.add(seeding_torrent)
        db_session.commit()

    with patch_torrents_status() as mock_status:
        with next(iter_sessions) as db_session:
            db_session.add(seeding_torrent)
            mock_status.return_value = get_seeding_torrents_info(
                (seeding_torrent.torrent_id,)
            )
            now = dt.datetime.utcnow()
            db_seeding_torrents = split_ready_db_torrents_by_state(db_session)[
                StateChoices.SEED
            ]
            client_torrents = deluge_client.decode_torrent_data(
                deluge_client.get_torrents_status(*TORRENTS_STATUS_DEFAULT_ARGS)
            )
            check_seeding_torrents(db_session, db_seeding_torrents, client_torrents)
            xseed = (
                db_session.execute(get_x_seed_query(seeding_torrent.torrent_id))
                .scalars()
                .first()
            )
            assert (
                now <= xseed.last_check < (later := now + dt.timedelta(seconds=30)),
                f"last_check: {xseed.last_check} is either less than now ({now}) or not higher than {later}",
            )
            assert (
                (past := now + dt.timedelta(seconds=30))
                < xseed.next_check
                <= (later := now + dt.timedelta(minutes=1, seconds=30)),
                f"next_check: {xseed.next_check} is not either too early ({past}) or not higher than {later}",
            )


        with next(iter_sessions) as db_session:
            assert not (db_session.execute(query).scalars().first())
            db_seeding_torrents = split_ready_db_torrents_by_state(db_session)[
                StateChoices.SEED
            ]
            client_torrents = deluge_client.decode_torrent_data(
                deluge_client.get_torrents_status(*TORRENTS_STATUS_DEFAULT_ARGS)
            )
            check_seeding_torrents(db_session, db_seeding_torrents, client_torrents)
            assert db_session.execute(query).scalars().first()
