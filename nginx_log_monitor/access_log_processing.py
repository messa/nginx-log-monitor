from asyncio import Queue
from logging import getLogger


logger = getLogger(__name__)


async def process_access_log_queue(conf, queue):
    assert isinstance(queue, Queue)


