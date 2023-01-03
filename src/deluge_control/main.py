import asyncio
import logging
import signal
from deluge_control.check_torrents import check_continuously
from deluge_control.download_torrents import download_torrents, get_aio_downloader
from deluge_control.register_torrents import register_continuously


async def close_connection_and_exit():
    try:
        aio_downloader = get_aio_downloader()
        if not aio_downloader.is_stopped_or_stopping:
            await aio_downloader.close()
    except:
        logging.exception("COULD NOT CLOSE RABBITMQ CONNECTION")
    finally:
        asyncio.get_event_loop().stop()


async def run():
    asyncio.create_task(download_torrents())
    asyncio.create_task(check_continuously(default_interval=60 * 10))
    asyncio.create_task(register_continuously())


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    for signame in ("SIGINT", "SIGTERM"):
        loop.add_signal_handler(
            getattr(signal, signame),
            lambda: asyncio.create_task(close_connection_and_exit()),
        )
    loop.create_task(run())
    loop.run_forever()
