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
                '301': 0,
                '304': 0,
                '308': 0,
                '400': 0,
                '404': 1,
                '500': 1,
                '502': 0,
                '504': 0,
            },
            'last_5_min': {
                '200': 3,
                '301': 0,
                '304': 0,
                '308': 0,
                '400': 0,
                '404': 1,
                '500': 1,
                '502': 0,
                '504': 0,
            },
        },
    }


def test_status_stats_report_dict_is_ordered():
    s = StatusStats()
    report = s.get_report()
    assert list(report['status_count']['total'].keys()) == ['200', '301', '304', '308', '400', '404', '500', '502', '504']
    assert list(report['status_count']['last_5_min'].keys()) == ['200', '301', '304', '308', '400', '404', '500', '502', '504']


def test_status_stats_rolling():
    s = StatusStats()
    mk_rec = lambda data: AccessLogRecord(data.get)
    s.update(mk_rec({'path': '/foo', 'status': 200}), now=10)
    s.update(mk_rec({'path': '/foo', 'status': 404}), now=20)
    assert s.get_report(now=315) == {
        'status_count': {
            'total': {
                '200': 1,
                '301': 0,
                '304': 0,
                '308': 0,
                '400': 0,
                '404': 1,
                '500': 0,
                '502': 0,
                '504': 0,

            },
            'last_5_min': {
                '200': 0,
                '301': 0,
                '304': 0,
                '308': 0,
                '400': 0,
                '404': 1,
                '500': 0,
                '502': 0,
                '504': 0,
            },
        },
    }
