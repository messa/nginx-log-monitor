from asyncio import Queue
from inspect import iscoroutinefunction
from weakref import WeakSet


def run_polyfill(f):
    '''
    Polyfill for asyncio.run() for Python < 3.7
    '''
    from asyncio import get_event_loop
    assert iscoroutinefunction(f)
    loop = get_event_loop()
    loop.run_until_complete(f)


class PubSub:

    def __init__(self, maxsize=0):
        self.queues = WeakSet()
        self.maxsize = maxsize

    def subscribe(self):
        q = Queue(self.maxsize)
        self.queues.add(q)
        return q

    async def put(self, item):
        for q in self.queues:
            await q.put(item)

