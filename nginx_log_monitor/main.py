from argparse import ArgumentParser
from asyncio import run, Queue, create_task, wait, FIRST_COMPLETED, CancelledError
from logging import getLogger
import os
from pathlib import Path
import yaml

from .configuration import Configuration
from .file_reader import tail_files
from .access_log_processing import process_access_log_queue


logger = getLogger(__name__)


def nginx_log_monitor_main():
    p = ArgumentParser()
    p.add_argument('--conf', metavar='FILE', help='path to configuration file')
    p.add_argument('--verbose', '-v', action='store_true')
    args = p.parse_args()
    setup_logging(verbose=args.verbose)
    cfg_path = args.conf or os.environ.get('CONF_FILE')
    cfg = yaml.safe_load(Path(cfg_path).read_text()) if cfg_path else {}
    conf = Configuration(cfg)
    run(async_main(conf))


log_format = '%(asctime)s %(name)-25s %(levelname)5s: %(message)s'


def setup_logging(verbose):
    from logging import basicConfig, DEBUG, WARNING
    basicConfig(
        format=log_format,
        level=DEBUG if verbose else WARNING)


async def async_main(conf):
    access_log_queue = Queue(1000)
    tasks = []
    run_task = lambda tf: tasks.append(create_task(tf))
    try:
        run_task(tail_files(access_log_queue, conf.get_access_log_paths))
        run_task(process_access_log_queue(conf, access_log_queue))
        await wait(tasks, return_when=FIRST_COMPLETED)
    finally:
        await stop_tasks(tasks)


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
