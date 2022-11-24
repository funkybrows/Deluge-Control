import asyncio
import logging

from deluge_control.check_torrents import check_continuously
from deluge_control.client import DelugeClient
from deluge_control.register_torrents import register_continuously


async def main():
    logging.debug("STARTING DELUGE_CONTROL")
    register_task = asyncio.create_task(register_continuously())
    logging.debug("CREATED REGISTER TASK")
    check_task = asyncio.create_task(check_continuously())
    await register_task
    await check_task


if __name__ == "__main__":
    asyncio.run(main())
