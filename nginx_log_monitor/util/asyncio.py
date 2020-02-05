from asyncio import get_event_loop
from inspect import iscoroutinefunction


def run_polyfill(f):
    '''
    Polyfill for asyncio.run() for Python < 3.7
    '''
    assert iscoroutinefunction(f)
    loop = get_event_loop()
    loop.run_until_complete(f)
