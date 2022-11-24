import asyncio
import datetime as dt
import os
import logging

from sqlalchemy.sql.expression import select

from .client import DelugeClient
from .models import Torrent, StateChoices
from .session import get_session

logger = logging.getLogger("deluge.register")


def register_new_torrents(deluge_client, session):
    torrent_info = deluge_client.decode_torrent_data(
        deluge_client.get_torrents_status(["state", "name", "time_added"])
    )
    new_torrents = []
    with session.begin():
        results = [
            unparsed_result.torrent_id
            for unparsed_result in session.execute(
                select(Torrent.torrent_id).where(
                    Torrent.torrent_id.in_(list(torrent_info.keys()))
                )
            ).all()
        ]

    for torrent_id in torrent_info:
        if torrent_id not in results:
            logger.info(
                "ADDING TORRENT %s WITH NAME: %s, STATE: %s, TIME_ADDED: %s",
                torrent_id,
                torrent_name := torrent_info[torrent_id]["name"],
                torrent_state := torrent_info[torrent_id]["state"],
                (
                    torrent_time_added := (
                        dt.datetime.fromtimestamp(
                            torrent_info[torrent_id]["time_added"]
                        )
                    )
                ).strftime("%Y:%m:%d @ %H:%M:%S"),
            )
            try:
                session.add(
                    new_torrent := Torrent(
                        torrent_id=torrent_id,
                        name=torrent_name,
                        state=StateChoices(torrent_state),
                        time_added=torrent_time_added,
                    )
                )
            except:
                logger.exception()
            else:
                new_torrents.append(new_torrent)
    try:
        session.commit()
        return new_torrents
    except:
        logger.exception()
        session.rollback()
        return []


async def register_continuously(default_interval=60):
    deluge_client = DelugeClient()
    await deluge_client.connect_with_retry()
    while True:
        logger.debug(
            f"Checking for new torrents as of {dt.datetime.utcnow().strftime('%H:%M:%S')}"
        )
        register_new_torrents(deluge_client, get_session()())
        logger.debug(
            f"Waiting until {(dt.datetime.utcnow() + dt.timedelta(seconds=60)).strftime('%H:%M:%S')} to check for new torrents"
        )
        await asyncio.sleep(60)
