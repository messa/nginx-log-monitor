from collections import Counter, defaultdict, deque
from logging import getLogger
import re
from sys import intern
from time import monotonic as monotime


logger = getLogger(__name__)


class PathStats:

    def __init__(self):
        self.total_path_status_count = defaultdict(Counter)
        self.rolling_5min_path_status_count = defaultdict(Counter)
        self.rolling_5min_deque = deque()

    def update(self, access_log_record, now=None):
        status = intern(str(access_log_record.status))
        path = unify_path(access_log_record.path)
        if access_log_record.host:
            path = access_log_record.host + path
        now = monotime() if now is None else now
        self.total_path_status_count[status][path] += 1
        self.rolling_5min_path_status_count[status][path] += 1
        self.rolling_5min_deque.append((now, status, path))
        self._roll(now)
        self._compact(status=status)

    def _roll(self, now):
        while self.rolling_5min_deque:
            t, status, unified_path = self.rolling_5min_deque[0]
            if t >= now - 300:
                break
            if self.rolling_5min_path_status_count[status][unified_path] > 0:
                self.rolling_5min_path_status_count[status][unified_path] -= 1
            self.rolling_5min_deque.popleft()

    def _compact(self, status):
        self.total_path_status_count[status] = cleanup_counter(self.total_path_status_count[status], 10000)
        self.rolling_5min_path_status_count[status] = cleanup_counter(self.rolling_5min_path_status_count[status], 10000)

    def get_report(self, now=None):
        now = monotime() if now is None else now
        self._roll(now)
        report = {
            'path_status_count': {
                'total': {},
                'last_5_min': {},
            },
        }

        for status, path_count in sorted(self.total_path_status_count.items()):
            assert status not in report['path_status_count']['total']
            report['path_status_count']['total'][status] = {}
            for path, count in path_count.most_common(5):
                report['path_status_count']['total'][status][path] = count

        for status, path_count in sorted(self.rolling_5min_path_status_count.items()):
            assert status not in report['path_status_count']['last_5_min']
            report['path_status_count']['last_5_min'][status] = {}
            for path, count in path_count.most_common(5):
                report['path_status_count']['last_5_min'][status][path] = count

        return report


def cleanup_counter(counter, size):
    assert isinstance(counter, Counter)
    if len(counter) < size * 1.5:
        return counter
    return Counter(dict(counter.most_common(size)))


def unify_path(path):
    assert isinstance(path, str)
    orig_path = path
    path = path.split('?')[0]
    path = re.sub(r'(/)[0-9a-f]{32}(/|$)', r'\1<uuid>\2', path)
    path = re.sub(r'(/)[0-9A-F]{32}(/|$)', r'\1<UUID>\2', path)
    path = re.sub(r'(/)[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(/|$)', r'\1<uuid>\2', path)
    path = re.sub(r'(/)[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}(/|$)', r'\1<UUID>\2', path)
    path = re.sub(r'(/)[0-9]+(/|$)', r'\1<n>\2', path)
    logger.debug('unify_path %r -> %r', orig_path, path)
    return path
