from asyncio import get_running_loop
from logging import getLogger
from glob import glob
from pathlib import Path


logger = getLogger(__name__)


class Configuration:

    def __init__(self, cfg):
        self.access_log_paths = []
        if cfg.get('access_logs'):
            self.access_log_paths.extend(cfg['access_logs'])
        self.overwatch = Overwatch(cfg.get('overwatch') or {})
        self.sentry = Sentry(cfg.get('sentry') or {})

    async def get_access_log_paths(self):
        loop = get_running_loop()
        await loop.run_in_executor(None, self.get_access_log_paths_sync())

    def get_access_log_paths_sync(self):
        if not self.access_log_paths:
            return Path('/var/log/nginx/access.log')
        paths = []
        for x in self.access_log_paths:
            paths.extend(glob(str(x)))
        return paths


class Overwatch:

    def __init__(self, cfg):
        self.report_url = None
        self.report_token = None
        if cfg.get('report_url') and cfg.get('report_token'):
            self.report_url = cfg['report_url']
            self.report_token = cfg['report_token']


class Sentry:

    def __init__(self, cfg):
        self.dsn = cfg.get('dsn')