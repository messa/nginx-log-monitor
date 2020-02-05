from argparse import ArgumentParser
from asyncio import Queue, wait, FIRST_COMPLETED, CancelledError
from logging import getLogger
import os
from pathlib import Path
import yaml

from .configuration import Configuration
from .file_reader import tail_files
from .access_log_parser import parse_access_log_line
from .util import asyncio_run, create_task
from .status_stats import StatusStats
from .path_stats import PathStats
from .overwatch import report_to_overwatch
from .sentry import report_to_sentry


logger = getLogger(__name__)


def nginx_log_monitor_main():
    '''
    Main entry point from __main__ or console script
    '''
    p = ArgumentParser()
    p.add_argument('--conf', metavar='FILE', help='path to configuration file')
    p.add_argument('--verbose', '-v', action='store_true')
    args = p.parse_args()
    setup_logging(verbose=args.verbose)
    cfg_path = args.conf or os.environ.get('CONF_FILE')
    cfg = yaml.safe_load(Path(cfg_path).read_text()) if cfg_path else {}
    conf = Configuration(cfg)
    asyncio_run(async_main(conf))


log_format = '%(asctime)s %(name)-25s %(levelname)5s: %(message)s'


def setup_logging(verbose):
    from logging import basicConfig, DEBUG, WARNING
    basicConfig(
        format=log_format,
        level=DEBUG if verbose else WARNING)


async def async_main(conf):
    '''
    This is where all the stuff is happening :)
    '''
    access_log_pubsub = PubSub(1000)

    tasks = []
    run_task = lambda tf: tasks.append(create_task(tf))
    try:
        run_task(tail_files(conf.get_access_log_paths, partial(process_log_line, access_log_pubsub)))
        status_stats = StatusStats()
        path_stats = PathStats()
        run_task(update_stats(access_log_pubsub.subscribe(), status_stats))
        run_task(update_stats(access_log_pubsub.subscribe(), path_stats))
        if conf.overwatch.enabled:
            run_task(report_to_overwatch(conf, status_stats, path_stats))
        if conf.sentry.enabled:
            run_task(report_to_sentry(conf, access_log_pubsub.subscribe()))
        await wait(tasks, return_when=FIRST_COMPLETED)
    finally:
        await stop_tasks(tasks)


async def process_log_line(access_log_pubsub, path, line):
    assert isinstance(line, bytes)
    line = line.decode()
    access_log_record = parse_access_log_line(line)
    await access_log_pubsub.put(access_log_record)


async def update_stats(access_log_queue, stats_obj):
    while True:
        access_log_record = await access_log_queue.get()
        stats.update(access_log_record)


async def stop_tasks(tasks):
    for t in tasks:
        cancel_task(t)
    for t in tasks:
        await get_task_result(t)


def cancel_task(t):
    if not t.done():
        logger.debug('Cancelling task %s', t)
        t.cancel()


async def get_task_result(t):
    try:
        await t
    except CancelledError as e:
        logger.debug('Task %r cancelled', t)
    except Exception as e:
        logger.debug('Task %r: %r', t, e)
