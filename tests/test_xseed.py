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


def test_generate_xseed(deluge_client, movie_names, db_5_sessions):
    """
    If one doesn't exist, we should generate an xseed obj for a seeding
    torrent.
    """
    iter_sessions = iter(db_5_sessions)
    torrent_id = "abc123"
    with next(iter_sessions) as db_session:
        torrent = Torrent(
            torrent_id=torrent_id, name=movie_names[0], state=StateChoices.SEED
        )
        db_session.add(torrent)
        db_session.commit()

    with patch_torrents_status() as mock_status:
        mock_status.return_value = get_seeding_torrents_info((torrent_id,))
        query = (
            select(TorrentXSeed)
            .join(Torrent.xseeds)
            .where(Torrent.id == TorrentXSeed.torrent_id)
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
