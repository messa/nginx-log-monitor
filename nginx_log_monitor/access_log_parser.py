'''
The main function in this module is parse_access_log_line().
'''

from datetime import datetime, timezone, timedelta
from functools import lru_cache
from logging import getLogger
import pytz
import re


logger = getLogger(__name__)


class InvalidLogFormatError (Exception):
    pass


class InvalidLogLineError (Exception):
    pass


nginx_log_formats = [
    # the brackets are unnecessary here but they make this list more readable
    (
        # the default predefined combined access log format
        '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent '
        '"$http_referer" "$http_user_agent"'

    ), (
        # log_format compression from the official documentation
        # https://docs.nginx.com/nginx/admin-guide/monitoring/logging/#setting-up-the-access-log
        '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent '
        '"$http_referer" "$http_user_agent" "$gzip_ratio"'

    ), (
        # Messa personal access log format :) but I think I copied from somewhere
        '$host $remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent '
        '"$http_referer" "$http_user_agent" $request_time $upstream_response_time $pipe'
    ),
]


ipv4_regex = r'[012]?[0-9]?[0-9]\.[012]?[0-9]?[0-9]\.[012]?[0-9]?[0-9]\.[012]?[0-9]?[0-9]'


log_format_parts_to_regex = {
    ' ': ' ',
    '-': '-',
    '$remote_addr': r'(?P<remote_addr>{ipv4_regex})'.format(ipv4_regex=ipv4_regex),
    '$remote_user': r'(?P<remote_user>[^ ]+)',
    '[$time_local]': r'\[(?P<time_local>[^]]+)\]',
    '"$request"': r'"(?P<method>[A-Z]+) (?P<path>/[^ "]*) (?P<protocol>HTTP/[0-9.]+)"',
    '$status': r'(?P<status>[0-9]{3})',
    '$body_bytes_sent': r'(?P<body_bytes_sent>[0-9]+)',
    '"$http_referer"': r'"(?P<referer>[^"]+)"',
    '"$http_user_agent"': r'"(?P<user_agent>[^"]+)"',
    '"$gzip_ratio"': r'"(?P<gzip_ratio>[0-9]+[,.][0-9]+)"',
    '$request_time': r'(?P<request_time>[0-9]+[,.][0-9]+)',
    '$upstream_response_time': r'(?P<upstream_response_time>[0-9]+[,.][0-9]+)',
    '$pipe': r'(?P<pipe_flag>[.p])',
    '$host': r'(?P<host>[^ ]+)',
}


def log_format_to_regex(log_format):
    assert isinstance(log_format, str)
    remaining = log_format
    full_regex = ''
    while remaining:
        for k in log_format_parts_to_regex:
            if remaining.startswith(k):
                remaining = remaining[len(k):]
                full_regex += log_format_parts_to_regex[k]
                break
        else:
            raise InvalidLogFormatError('Cannot convert log format part to regex: {!r}'.format(remaining))
    full_regex = '^' + full_regex + '$'
    #logger.debug('log_format_to_regex(%r) -> %r', log_format, full_regex)
    return full_regex


def _re_compile(regex):
    assert isinstance(regex, str)
    try:
        return re.compile(regex)
    except Exception as e:
        raise InvalidLogFormatError('Failed to compile regular expression: {!r} - {}'.format(regex, e))


@lru_cache()
def get_nginx_log_format_compiled_regexes():
    return [_re_compile(log_format_to_regex(s)) for s in nginx_log_formats]


# code before this line prepares the regexes for log line parsing
# -----------------------------------------------------------------------------------------------
# code after this line does the log line parsing (executing regexes & postprocessing)


def parse_access_log_line(line):
    '''
    Convert log line string into AccessLogRecord object.
    See tests/test_log_parsing.py.
    '''
    assert isinstance(line, str)
    regexes = get_nginx_log_format_compiled_regexes()
    for regex in regexes:
        m = regex.match(line)
        #logger.debug('regex: %r line: %r -> %r', regex, line, m)
        if m:
            return AccessLogRecord(m.groupdict().get)
    raise InvalidLogLineError('Could not recognize log format: {!r}'.format(line))


class AccessLogRecord:

    # This could be namedtuple, but we want to keep it mutable to make any
    # eventual postprocessing easier.

    def __init__(self, get):
        self.host = get('host')
        self.remote_addr = get('remote_addr')
        self.remote_user = dash_to_none(get('remote_user'))
        time_local = get('time_local')
        if time_local:
            self.date_str = time_local
            self.date_local = parse_date(time_local)
            self.date_utc = date_to_utc(self.date_local)
        else:
            self.date_str = None
            self.date_local = None
            self.date_utc = None
        self.method = get('method')
        self.path = get('path')
        self.protocol = get('protocol')
        self.status = int(get('status'))
        self.body_bytes_sent = int(get('body_bytes_sent'))
        self.referer = dash_to_none(get('referer'))
        self.user_agent_str = get('user_agent')
        self.request_time = _float(get('request_time'))
        self.upstream_response_time = _float(get('upstream_response_time'))
        pipe_flag = get('pipe_flag')
        if pipe_flag == 'p':
            self.pipelined = True
        elif pipe_flag == '.':
            self.pipelined = False
        else:
            self.pipelined = None

    def __repr__(self):
        return '<{cls} method={s.method!r} path={s.path!r} status={s.status!r}>'.format(cls=self.__name__.__class__, s=self)


def _float(v):
    if v is None:
        return None
    return float(v)


def dash_to_none(s):
    if s == '-':
        return None
    else:
        return s


re_time_local = re.compile(
    # example: '04/Feb/2020:13:14:33 +0100'
    r'^([0123][0-9])/([A-Z][a-z][a-z])/([12][0-9]{3})'
    r':([012][0-9]):([0-5][0-9]):([0-6][0-9]) ([+-])([0-9]{2})([0-9]{2})$')


month_names = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()
month_name_to_number = {m: n for n, m in enumerate(month_names, start=1)}
assert len(month_name_to_number) == 12


def parse_date(date_str):
    m = re_time_local.match(date_str)
    if m:
        d, m, y, H, M, S, ts, tH, tM = m.groups()
        tz_offset = timedelta(hours=int(tH), minutes=int(tM))
        if ts == '-':
            tz_offset = - tz_offset
        return datetime(
            int(y), month_name_to_number[m], int(d),
            int(H), int(M), int(S),
            tzinfo=timezone(tz_offset))
    raise InvalidLogLineError('Unknown date format: {!r}'.format(date_str))


def date_to_utc(dt):
    return pytz.utc.normalize(dt)
