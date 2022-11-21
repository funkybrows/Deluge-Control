import logging

from sqlalchemy.sql.expression import select

from .models import Torrent, StateChoices

logger = logging.getLogger("Deluge")
logger.setLevel(logging.DEBUG)


def register_new_torrents(deluge_client, session):
    torrent_info = deluge_client.decode_torrent_data(
        deluge_client.get_torrents_status(["state"])
    )
    new_torrents = []
    with session.begin():
        results = session.execute(
            select(Torrent.torrent_id).where(
                Torrent.torrent_id.in_(list(torrent_info.keys()))
            )
        ).all()

    for torrent_id in torrent_info:
        if torrent_id not in results:
            try:
                logger.debug(
                    "ADDING TORRENT %s WITH NAME: %s, STATE: %s",
                    torrent_id,
                    torrent_name := torrent_info[torrent_id]["name"],
                    torrent_state := torrent_info[torrent_id]["state"],
                )
                session.add(
                    new_torrent := Torrent(
                        torrent_id=torrent_id,
                        name=torrent_name,
                        state=StateChoices(torrent_state),
                    )
                )
                new_torrents.append(new_torrent)
            except Exception as exc:
                logger.exception(exc)
                raise
    try:
        session.commit()
        return new_torrents
    except Exception as exc:
        logger.exception(exc)
        session.rollback()
        return []
