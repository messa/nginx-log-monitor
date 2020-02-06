from collections import Counter, defaultdict
from logging import getLogger
import re


logger = getLogger(__name__)


class PathStats:

    def __init__(self):
        self.path_status_count = defaultdict(Counter())

    def update(self, access_log_record):
        status = int(access_log_record.status)
        unified_path = unify_path(access_log_record.path)
        self.path_status_count[status][unified_path] += 1
        self.path_status_count[status] = cleanup_counter(self.path_status_count[status], 10000)

    def get_report(self):
        report = {
            'path_status_count': {},
        }
        for status, path_count in sorted(self.path_status_count.items()):
            report['path_status_count'].setdefault(status, {})
            for path, count in path_count.most_common(5):
                report['path_status_count'][status][path] = count
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
