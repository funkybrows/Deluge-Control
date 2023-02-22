import asyncio
import datetime as dt
import logging
from sqlalchemy.sql.expression import select
from .client import DelugeClient
from .models import StateChoices, Torrent, TorrentSnapshot
from .session import get_session

logger = logging.getLogger("deluge.check")


def split_ready_db_torrents_by_state(session: Session) -> Dict[str, Dict[str, Torrent]]:
    ready_torrents = (
        session.execute(
            select(Torrent).where(Torrent.next_check_time <= dt.datetime.utcnow())
        )
        .scalars()
        .all()
    )
    torrents = defaultdict(dict)
    for torrent in ready_torrents:
        torrents[torrent.state][torrent.torrent_id] = torrent
    return torrents


            )
        )
        update_seeding_torrents(seeding_torrents, torrent_info)
        new_torrent_snapshots = []
        now = dt.datetime.utcnow()
        next_check = now + dt.timedelta(seconds=60)
        for torrent in seeding_torrents:
            torrent_id = torrent.torrent_id
            logger.info(
                "ADDING SNAPSHOT %s FOR TORRENT: %s, TOTAL_UPLOAD: %s, SEEDS: %s, PEERS: %s",
                torrent.name,
                total_uploaded := torrent_info[torrent_id]["total_uploaded"],
                total_seeds := torrent_info[torrent_id]["total_seeds"],
                total_peers := torrent_info[torrent_id]["total_peers"],
                (time_recorded := now).strftime("%Y:%m:%d @ %H:%M:%S"),
            )
            try:
                session.add(
                    new_torrent_snapshot := (
                        TorrentSnapshot(
                            torrent=torrent,
                            total_uploaded=total_uploaded
                            / 1024
                            / 1024,  # Convert from byte to mega
                            total_seeds=total_seeds,
                            total_peers=total_peers,
                            time_recorded=time_recorded,
                        )
                    )
                )
                new_torrent_snapshot.torrent.next_check_time = next_check
            except Exception as exc:
                logger.exception(
                    "Could not add new torrent snapshot to session: torrent_id, %s",
                    torrent_id,
                )
            else:
                new_torrent_snapshots.append(new_torrent_snapshot)

        try:
            session.commit()
            return new_torrent_snapshots
        except Exception as exc:
            logger.exception("Could not commit during check_seeding_torrents")
            session.rollback()
            return []


async def check_continuously(default_interval=60):
    deluge_client = DelugeClient()
    await deluge_client.connect_with_retry()
    while True:
        logger.debug(
            f"Making snapshots for ready torrents as of {dt.datetime.utcnow().strftime('%H:%M:%S')}"
        )
        try:
            session = get_session()()
        except:
            logger.exception("COULD NOT CONNECT TO DB")
            raise
        else:
            check_seeding_torrents(deluge_client, session)
            logger.debug(
                f"Waiting until {(dt.datetime.utcnow() + dt.timedelta(seconds=60)).strftime('%H:%M:%S')} to make snapshots for ready torrents"
            )
            await asyncio.sleep(default_interval)
