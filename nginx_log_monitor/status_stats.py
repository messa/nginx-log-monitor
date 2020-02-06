from collections import Counter
from logging import getLogger


logger = getLogger(__name__)


class StatusStats:

    def __init__(self):
        self.status_count = Counter()

    def update(self, access_log_record):
        status = str(access_log_record.status)
        self.status_count[status] += 1

    def get_report(self):
        report = {
            'status_count': {},
        }
        for status, count in sorted(self.status_count.items()):
            report['status_count'][status] = count
        return report
