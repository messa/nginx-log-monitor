from argparse import ArgumentParser
from asyncio import run, Queue
import os
from pathlib import Path
import yaml

from .configuration import Configuration


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
    watch_
