from pathlib import Path


class Configuration:

    def __init__(self, cfg):
        self.access_log_paths = []
        if cfg.get('access_logs'):
            self.access_log_paths.extend(Path(p) for p in cfg.get('access_logs'))
