import asyncio
import datetime as dt
import logging
from typing import Dict, List, Union
from sqlalchemy.sql.expression import select
from sqlalchemy.orm.session import Session
from .client import DelugeClient
from .models import StateChoices, Torrent, TorrentRetry, TorrentSnapshot
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
def check_downloading_torrents(
    deluge_client,
    session: Session,
    db_downloading_torrents: Dict[str, Torrent],
    client_torrents: Dict[StateChoices, Dict[str, Union[str, int, float]]],
) -> List[Torrent]:
    reannounces = []
    logger.info("CHECKING DOWNLOADING TORRENTS")

    for download_torrent_id, download_torrent in db_downloading_torrents.items():
        if (client_torrent_info := client_torrents[download_torrent_id])[
            "progress"
        ] == 0 and client_torrent_info["total_seeds"] > 0:
            retry, created = TorrentRetry.get_or_create(session, download_torrent_id)
            if created:
                download_torrent.next_check_time += dt.timedelta(seconds=30)
            else:
                reannounces.append(download_torrent.torrent_id)
                retry.count += 1
                if retry.count > 1:
                    download_torrent.next_check_time += dt.timedelta(minutes=10)
                else:
                    download_torrent.next_check_time += dt.timedelta(minutes=2)
                session.add(download_torrent)

    if reannounces:
        logger.info("FORCING REANNOUNCE FOR %s", reannounces)
        try:
            deluge_client.force_reannounce(reannounces)
        except:
            logger.exception("ERROR: COULD NOT FORCE REANNOUNCE FOR %s", reannounces)
    return db_downloading_torrents.values()

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
