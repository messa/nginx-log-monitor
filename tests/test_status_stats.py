from nginx_log_monitor.access_log_parser import AccessLogRecord
from nginx_log_monitor.status_stats import StatusStats


def test_status_stats():
    s = StatusStats()
    mk_rec = lambda data: AccessLogRecord(data.get)
    s.update(mk_rec({'path': '/foo', 'status': 200}))
    s.update(mk_rec({'path': '/foo', 'status': 404}))
    s.update(mk_rec({'path': '/bar/1234', 'status': 200}))
    s.update(mk_rec({'path': '/bar/567', 'status': 200}))
    s.update(mk_rec({'path': '/bar/89', 'status': 500}))
    assert s.get_report() == {
        'status_count': {
            '200': 3,
            '404': 1,
            '500': 1,
        },
    }
