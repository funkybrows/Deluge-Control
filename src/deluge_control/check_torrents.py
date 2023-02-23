import asyncio
import datetime as dt
import logging
from collections import defaultdict
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


def update_torrent_states(
    session: Session,
    db_torrents: Dict[StateChoices, Dict[str, Torrent]],
    client_torrents: Dict[StateChoices, Dict[str, Union[str, int, float]]],
):
    logger.debug("UPDATING TORRENT STATES")
    state_changed_torrents = defaultdict(list)
    to_delete_torrent_ids = defaultdict(list)
    for db_state, state_torrents in db_torrents.items():
        for db_torrent_id, db_torrent in state_torrents.items():
            if (
                db_torrent_id not in client_torrents
                and db_torrent.state is not StateChoices.DEL
            ):
                logger.debug("CHANGING STATE OF %s TO DELETED", db_torrent.name)
                db_torrent.set_state("Deleted")
                session.add(db_torrent)
                to_delete_torrent_ids[db_state].append(db_torrent_id)
            elif (
                client_state := client_torrents[db_torrent.torrent_id]["state"]
            ) != db_state.value:
                logger.debug(
                    "CHANGING STATE OF %s TO %s", db_torrent.name, client_state
                )
                db_torrent.set_state(client_state)
                session.add(db_torrent)
                state_changed_torrents[db_state].append(
                    (db_torrent_id, db_state, client_state)
                )

    for state in tuple(db_torrents.keys()):
        for (torrent_id, old_state, new_state) in state_changed_torrents[state]:
            db_torrents[new_state][torrent_id] = db_torrents[old_state][torrent_id]
            del db_torrents[old_state][torrent_id]

    for state, state_deletes in to_delete_torrent_ids.items():
        for to_delete in state_deletes:
            del db_torrents[state][to_delete]


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


def check_seeding_torrents(
    session: Session,
    db_seeding_torrents: Dict[str, Torrent],
    client_torrents: Dict[StateChoices, Dict[str, Union[str, int, float]]],
):
    new_torrent_snapshots = []
    now = dt.datetime.utcnow()
    next_check = now + dt.timedelta(minutes=5)
    logger.info("CHECKING SEEDING TORRENTS")
    for torrent_id, torrent in db_seeding_torrents.items():
        torrent_info = client_torrents[torrent_id]
        logger.info(
            "ADDING SNAPSHOT %s FOR TORRENT: %s, TOTAL_UPLOAD: %s, SEEDS: %s, PEERS: %s",
            torrent.name,
            total_uploaded := torrent_info["total_uploaded"],
            total_seeds := torrent_info["total_seeds"],
            total_peers := torrent_info["total_peers"],
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

        return new_torrent_snapshots


# XXX: We'll eventually make the db operations async
def check_torrents(deluge_client: DelugeClient, session: Session):
    db_torrents = split_ready_db_torrents_by_state(session)
    torrent_ids = []
    for grouped_torrents_info in db_torrents.values():
        torrent_ids += list(grouped_torrents_info.keys())
    client_torrents = deluge_client.decode_torrent_data(
        deluge_client.get_torrents_status(
            ["progress", "state", "total_peers", "total_seeds", "total_uploaded"],
            id=torrent_ids,
        )
    )
    update_torrent_states(session, db_torrents, client_torrents)
    check_downloading_torrents(
        deluge_client, session, db_torrents[StateChoices.DL], client_torrents
    )
    check_seeding_torrents(session, db_torrents[StateChoices.SEED], client_torrents)


async def check_continuously(default_interval=60):
    deluge_client = DelugeClient()
    await deluge_client.connect_with_retry()
    while True:
        logger.debug(
            f"Making snapshots for ready torrents as of {dt.datetime.utcnow().strftime('%H:%M:%S')}"
        )
        try:
            session = get_session()
            with session.begin() as db_session:
                try:
                    check_torrents(deluge_client, db_session)
                except:
                    logger.exception("ERROR: FAILED TO CHECK TORRENTS")
                    db_session.rollback()
                else:
                    db_session.commit()
        except:
            logger.exception("COULD NOT CONNECT TO DB")
            raise
        else:
            logger.debug(
                f"Waiting until {(dt.datetime.utcnow() + dt.timedelta(seconds=60)).strftime('%H:%M:%S')} to check torrents again"
            )
            await asyncio.sleep(default_interval)
