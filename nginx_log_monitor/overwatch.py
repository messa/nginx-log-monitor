from asyncio import sleep
from datetime import datetime
from logging import getLogger
from os import getpid
from socket import getfqdn
from time import time

from .clients.overwatch_client import OverwatchClientNotConfiguredError, OverwatchClientReportError


logger = getLogger(__name__)

sleep_interval_s = 15


async def report_to_overwatch(conf, status_stats, path_stats, overwatch_client):
    while True:
        await sleep(sleep_interval_s)
        report = generate_report(status_stats, path_stats)
        try:
            await overwatch_client.send_report(report)
        except OverwatchClientNotConfiguredError:
            logger.info('Overwatch not configured')
        except OverwatchClientReportError as e:
            logger.warning('Overwatch report failed: %r', e)


def generate_report(status_stats, path_stats):
    watchdog_interval_s = sleep_interval_s * 2 + 60
    report = {
        'date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'label': {
            'agent': 'nginx_log_monitor',
            'host': getfqdn(),
        },
        'state': {
            'pid': getpid(),
            'watchdog': {
                '__watchdog': {
                    'deadline': int((time() + watchdog_interval_s) * 1000),
                },
            },
        }
    }
    report['state'].update(status_stats.get_report())
    report['state'].update(path_stats.get_report())
    return report
