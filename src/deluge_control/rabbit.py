import json
import logging
import os

from aio_pika_wrapper.client import AioClient, AsyncState

from deluge_control.client import get_deluge_client

logger = logging.getLogger("deluge.rpc")


class AioDownloader(AioClient):
    TIMEOUT = 5

    def __init__(
        self,
        exchange_name=f"{os.environ.get('PROJECT_NAME')}-{os.environ.get('NAMESPACE')}",
        client_name=None,
        pool=None,
    ):
        super().__init__(None, client_name, pool=pool)
        self.declare_exchange_name = (
            exchange_name  # not to be confused w/ AioPikaClient._exchange_name
        )
        self._queue = None

    async def connect(self):
        await super().connect()
        await self.wait_until_connected(timeout=self.TIMEOUT)
        exchange = await self.declare_exchange(
            self.declare_exchange_name,
            exchange_type="topic",
            durable=True,
            timeout=self.TIMEOUT,
        )
        if exchange:
            self.queue = await self.declare_queue(
                durable=True, exclusive=True, auto_delete=True, timeout=self.TIMEOUT
            )
            await self.bind_queue(
                self.queue.name,
                exchange_name=self.declare_exchange_name,
                routing_key="torrent.download.*.*",
            )
            await self.set_exchange(self.declare_exchange_name)

    async def start_consuming(self):
        async def callback(message):
            async with message.process():
                if message.content_type == "application/json":
                    logger.info(
                        "GOT MESSAGE: %s", message_info := json.loads(message.body)
                    )
                    try:
                        deluge_client = get_deluge_client()
                        deluge_client.add_torrent_url(
                            message_info["torrent_url"],
                            **message_info.get("download_options", {}),
                        )

                    except:
                        logger.exception(
                            "COULD NOT DOWNLOAD TORRENT: %s", message_info["name"]
                        )

        await super().start_consuming(self.queue.name, callback)

    async def wait_until_consuming(self, timeout=5):
        await self._wait_until_state(AsyncState.CONSUMING, timeout=timeout)
