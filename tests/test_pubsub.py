from pytest import mark

from nginx_log_monitor.util import PubSub


@mark.asyncio
async def test_pubsub():
    p = PubSub()
    await p.put('item1')
    q1 = p.subscribe()
    await p.put('item2')
    q2 = p.subscribe()
    await p.put('item3')

    assert dump_queue(q1) == ['item2', 'item3']
    assert dump_queue(q2) == ['item3']


def dump_queue(q):
    items = []
    while not q.empty():
        items.append(q.get_nowait())
    return items
