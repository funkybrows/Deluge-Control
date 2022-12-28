import asyncio
import os

from deluge_control.rabbit import AioDownloader

AIO_DOWNLOADER = None


def get_aio_downloader():
    global AIO_DOWNLOADER
    if not AIO_DOWNLOADER:
        AIO_DOWNLOADER = AioDownloader(
            exchange_name=os.environ.get("RABBIT_EXCHANGE"),
            client_name=f'{os.environ.get("PROJECT NAME", "Torrenting")} Downloader',
        )
    return AIO_DOWNLOADER
