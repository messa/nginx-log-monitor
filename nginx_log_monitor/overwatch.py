from asyncio import sleep, wait_for, TimeoutError
from collections import OrderedDict
from datetime import datetime
from logging import getLogger
import os
from os import getpid
from socket import getfqdn
from time import time

from .clients.overwatch_client import OverwatchClientNotConfiguredError, OverwatchClientReportError


logger = getLogger(__name__)


async def report_to_overwatch(conf, status_stats, path_stats, overwatch_client):
    while True:
        report = generate_report(conf, status_stats, path_stats)
        try:
            await overwatch_client.send_report(report)
        except OverwatchClientNotConfiguredError:
            logger.info('Overwatch not configured')
        except OverwatchClientReportError as e:
            logger.warning('Overwatch report failed: %r', e)
        if not status_stats.have_5xx.is_set():
            try:
                await wait_for(status_stats.have_5xx.wait(), conf.overwatch.report_interval_s)
            except TimeoutError:
                pass
        else:
            await sleep(conf.overwatch.report_interval_s)


def generate_report(conf, status_stats, path_stats):
    watchdog_interval_s = conf.overwatch.report_interval_s * 2 + 60
    report = {
        'date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'label': {
            'agent': 'nginx_log_monitor',
            'host': os.environ.get('LABEL_HOST') or getfqdn(),
        },
        'state': OrderedDict(),
    }
    report['state']['pid'] = getpid()
    report['state']['watchdog'] = {
        '__watchdog': {
            'deadline': int((time() + watchdog_interval_s) * 1000),
        },
    }
    report['state'].update(status_stats.get_report())
    report['state'].update(path_stats.get_report())
    return report
