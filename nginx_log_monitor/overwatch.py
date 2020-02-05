from asyncio import sleep
from aiohttp import ClientSession


sleep_interval_s = 30


async def report_to_overwatch(conf, status_stats, path_stats):
    async with ClientSession() as session:
        while True:
            await sleep(sleep_interval_s)

