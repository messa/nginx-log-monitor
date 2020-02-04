from datetime import datetime
import pytz

from nginx_log_monitor import parse_access_log_line


def test_sample_nginx_access_log():
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

