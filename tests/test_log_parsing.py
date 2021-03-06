from asyncio import Queue, gather
from datetime import datetime
from pytest import mark
import pytz
from time import monotonic as monotime

from nginx_log_monitor import parse_access_log_line


def test_default_nginx_access_log():
    line = '84.22.97.60 - - [04/Feb/2020:11:02:10 +0000] "GET / HTTP/1.1" 200 396 "-" "Mozilla/5.0 zgrab/0.x"'
    rec = parse_access_log_line(line)
    assert rec.remote_addr == '84.22.97.60'
    assert rec.date_utc == pytz.utc.localize(datetime(2020, 2, 4, 11, 2, 10))
    assert rec.method == 'GET'
    assert rec.path == '/'
    assert rec.protocol == 'HTTP/1.1'
    assert rec.status == 200
    assert rec.body_bytes_sent == 396
    assert rec.referer == None
    assert rec.user_agent_str == 'Mozilla/5.0 zgrab/0.x'


def test_custom_nginx_access_log_20200220():
    line = (
        'example.com 1.23.45.67 - - [20/Feb/2020:11:15:26 +0100] '
        '"GET /foo HTTP/1.1" 404 197 "-" "Mozilla/5.0 ..." 0.000 - .'
    )
    rec = parse_access_log_line(line)
    assert rec.upstream_response_time is None


def test_custom_nginx_access_log_20200204():
    line = (
        'foo.example.com 123.45.6.78 - - [04/Feb/2020:13:50:33 +0100] '
        '"POST /api/todo/list HTTP/2.0" 200 2702 '
        '"https://foo.example.com/todos" '
        '"Mozilla/5.0 (Windows NT 10.0; Win64; x64) ... Safari/537.36" '
        '0.206 0.206 .'
    )
    # Corresponding nginx configuration:
    #   log_format custom '$host '
    #                     '$remote_addr - $remote_user [$time_local] '
    #                     '"$request" $status $body_bytes_sent '
    #                     '"$http_referer" "$http_user_agent" '
    #                     '$request_time $upstream_response_time $pipe';
    #   access_log /var/log/nginx/access.log custom;
    rec = parse_access_log_line(line)
    assert rec.host == 'foo.example.com'
    assert rec.remote_addr == '123.45.6.78'
    assert rec.remote_user == None
    assert rec.date_utc == pytz.utc.localize(datetime(2020, 2, 4, 12, 50, 33))
    assert rec.method == 'POST'
    assert rec.path == '/api/todo/list'
    assert rec.protocol == 'HTTP/2.0'
    assert rec.status == 200
    assert rec.body_bytes_sent == 2702
    assert rec.referer == 'https://foo.example.com/todos'
    assert rec.user_agent_str == 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ... Safari/537.36'
    assert rec.request_time == 0.206
    assert rec.upstream_response_time == 0.206
    assert rec.pipelined == False


def test_default_nginx_access_log_benchmark():
    count = 1000
    t0 = monotime()
    for i in range(count):
        line = '84.22.97.60 - - [04/Feb/2020:11:02:10 +0000] "GET /{i} HTTP/1.1" 200 396 "-" "Mozilla/5.0 foo/{i}"'.format(i=i)
        rec = parse_access_log_line(line)
    duration = monotime() - t0
    assert duration < 0.1


@mark.asyncio
async def test_default_nginx_access_log_benchmark_with_asyncio_queue():
    count = 1000
    q = Queue()

    async def produce():
        for i in range(count):
            line = '84.22.97.60 - - [04/Feb/2020:11:02:10 +0000] "GET /{i} HTTP/1.1" 200 396 "-" "Mozilla/5.0 foo/{i}"'.format(i=i)
            await q.put(line)
        await q.put(None)

    async def consume():
        for i in range(count):
            line = await q.get()
            parse_access_log_line(line)
        last = await q.get()
        assert last is None

    t0 = monotime()
    await gather(produce(), consume())
    duration = monotime() - t0
    assert duration < 0.1
