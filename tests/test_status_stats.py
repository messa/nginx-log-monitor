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
            'total': {
                '200': 3,
                '404': 1,
                '500': 1,
            },
            'last_5_min': {
                '200': 3,
                '404': 1,
                '500': 1,
            },
        },
    }


def test_status_stats_rolling():
    s = StatusStats()
    mk_rec = lambda data: AccessLogRecord(data.get)
    s.update(mk_rec({'path': '/foo', 'status': 200}), now=10)
    s.update(mk_rec({'path': '/foo', 'status': 404}), now=20)
    assert s.get_report(now=315) == {
        'status_count': {
            'total': {
                '200': 1,
                '404': 1,
            },
            'last_5_min': {
                '200': 0,
                '404': 1,
            },
        },
    }
