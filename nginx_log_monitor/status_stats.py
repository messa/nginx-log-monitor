from collections import OrderedDict, Counter, deque
from logging import getLogger
from sys import intern
from time import monotonic as monotime


logger = getLogger(__name__)

basic_status_codes = '200 301 304 308 400 404 500 502 504'.split()


class StatusStats:

    def __init__(self):
        self.total_status_count = Counter()
        self.rolling_5min_status_count = Counter()
        self.rolling_5min_deque = deque()
        for status in sorted(basic_status_codes):
            status = intern(str(status))
            self.total_status_count[status] = 0
            self.rolling_5min_status_count[status] = 0

    def update(self, access_log_record, now=None):
        status = intern(str(access_log_record.status))
        now = monotime() if now is None else now
        self.total_status_count[status] += 1
        self.rolling_5min_status_count[status] += 1
        self.rolling_5min_deque.append((now, status))
        self._roll(now)

    def _roll(self, now):
        while self.rolling_5min_deque:
            t, status = self.rolling_5min_deque[0]
            if t >= now - 300:
                break
            self.rolling_5min_status_count[status] -= 1
            self.rolling_5min_deque.popleft()

    def get_report(self, now=None):
        now = monotime() if now is None else now
        self._roll(now)
        report = OrderedDict()
        report['status_count'] = OrderedDict()
        report['status_count']['total'] = OrderedDict()
        report['status_count']['last_5_min'] = OrderedDict()
        for status, count in sorted(self.total_status_count.items()):
            report['status_count']['total'][status] = count
        for status, count in sorted(self.rolling_5min_status_count.items()):
            report['status_count']['last_5_min'][status] = count
        return report
