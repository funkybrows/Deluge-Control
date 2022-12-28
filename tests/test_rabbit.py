import asyncio
import datetime as dt
import os
import logging
from unittest import mock

import pytest
from tenacity import retry, stop_after_attempt, wait_fixed
from aio_pika_wrapper.client import AioClient, AioConnectionPool
from deluge_control.client import get_deluge_client
from deluge_control.rabbit import AioDownloader
from deluge_control import utils

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)

LOGGER = logging.getLogger(__name__)
AIO_CLIENT_LOGGER = logging.getLogger("aio_pika_wrapper.client")
handler = logging.FileHandler(f"{utils.get_log_folder_path()}/debug.log", mode="w")
LOGGER.setLevel(logging.DEBUG)
LOGGER.addHandler(handler)
AIO_CLIENT_LOGGER.setLevel(logging.DEBUG)
AIO_CLIENT_LOGGER.addHandler(handler)
RPC_LOGGER = logging.getLogger("deluge.rpc")
RPC_LOGGER.setLevel(logging.DEBUG)
RPC_LOGGER.addHandler(handler)
DELUGE_CLIENT_LOGGER = logging.getLogger("deluge.client")
DELUGE_CLIENT_LOGGER.setLevel(logging.DEBUG)
DELUGE_CLIENT_LOGGER.addHandler(handler)

MESSAGE = {
    "name": "Abbott Elementary S02E07 1080p x265-Elite",
    "torrent_url": os.environ.get(
        "TEST_TL_TORRENT_URL",
        "'https://www.torrentleech.org/rss/download/123456789/1234a12abcde1ab1a123/Abbott+Elementary+S02E07+1080p+x265-Elite.torrent",
    ),
    "date": dt.datetime.now().isoformat(),
    "indexer": "TL",
}


@mock.patch("deluge_control.client.DelugeClient.add_torrent_url")
@pytest.mark.asyncio
async def test_download_torrent(mock_add_torrent):
    @retry(reraise=True, stop=stop_after_attempt(3), wait=wait_fixed(3))
    async def assert_w_retry():
        mock_add_torrent.assert_called_with(MESSAGE["torrent_url"])

    pool = AioConnectionPool(3)
    aio_consumer = AioDownloader(
        exchange_name="test-exchange", client_name="Test_Download", pool=pool
    )
    await aio_consumer.wait_until_ready(timeout=5)
    asyncio.create_task(aio_consumer.start_consuming())
    await aio_consumer.wait_until_consuming()
    aio_publisher = AioClient("test-exchange", client_name="TestPublisher", pool=pool)
    await aio_publisher.wait_until_ready()
    await aio_publisher.publish_message(
        "torrent.download.url.tl", MESSAGE, content_type="application/json"
    )
    try:
        await assert_w_retry()
    finally:
        await aio_consumer.delete_exchange("test-exchange", if_unused=False)
        await pool.close()


@pytest.mark.asyncio
async def test_download_real_torrent():
    if not os.environ.get("TEST_TL_TORRENT_URL"):
        assert False, "NO TEST_TL_TORRENT_URL"
    deluge_client = get_deluge_client()

    def get_torrent_id():
        torrents = deluge_client.get_torrents_status(("name",))
        torrent_data = deluge_client.decode_torrent_data(torrents)
        for torrent_id, values in torrent_data.items():
            if "Abbott.Elementary.S02E07" in values["name"]:
                return torrent_id

    def cleanup_client():
        torrent_id = get_torrent_id()
        if torrent_id:
            deluge_client.remove_torrent(torrent_id, remove_data=False)

    @retry(reraise=True, stop=stop_after_attempt(3), wait=wait_fixed(3))
    async def assert_w_retry():
        assert get_torrent_id()

    cleanup_client()
    pool = AioConnectionPool(3)
    aio_consumer = AioDownloader(
        exchange_name="test-exchange", client_name="Test_Download", pool=pool
    )
    await aio_consumer.wait_until_ready(timeout=5)
    asyncio.create_task(aio_consumer.start_consuming())
    await aio_consumer.wait_until_consuming()
    aio_publisher = AioClient("test-exchange", client_name="TestPublisher", pool=pool)
    await aio_publisher.wait_until_ready()
    await aio_publisher.publish_message(
        "torrent.download.url.tl",
        {**MESSAGE, "download_options": {"add_in_paused_state": True}},
        content_type="application/json",
    )
    try:
        await assert_w_retry()
    finally:
        await aio_consumer.delete_exchange("test-exchange", if_unused=False)
        await pool.close()
