from logging import getLogger
from glob import glob
from pathlib import Path
import yaml


logger = getLogger(__name__)


class Configuration:

    def __init__(self, cfg_path):
        if cfg_path:
            logger.debug('Loading configuration from %s', cfg_path)
            cfg = yaml.safe_load(Path(cfg_path).read_text())
        else:
            cfg = {}
        self.access_log_paths = []
        if cfg.get('access_logs'):
            self.access_log_paths.extend(cfg['access_logs'])
        self.overwatch = Overwatch(cfg.get('overwatch') or {})
        self.sentry = Sentry(cfg.get('sentry') or {})

    def get_access_log_paths(self):
        if not self.access_log_paths:
            return [Path('/var/log/nginx/access.log')]
        paths = []
        for x in self.access_log_paths:
            paths.extend(Path(p) for p in glob(str(x)))
        return paths


class Overwatch:

    default_report_interval_s = 30

    def __init__(self, cfg):
        self.report_url = None
        self.report_token = None
        self.enabled = False
        if cfg.get('report_url') and cfg.get('report_token'):
            self.report_url = cfg['report_url']
            self.report_token = cfg['report_token']
            self.enabled = cfg.get('enabled', True)
        self.report_interval_s = float(cfg.get('report_interval_s') or self.default_report_interval_s)


class Sentry:

    def __init__(self, cfg):
        self.dsn = cfg.get('dsn')
        self.enabled = bool(self.dsn) and cfg.get('enabled', True)
