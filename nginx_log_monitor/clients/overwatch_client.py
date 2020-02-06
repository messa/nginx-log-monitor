from aiohttp import ClientSession
from logging import getLogger
from reprlib import repr as smart_repr


logger = getLogger(__name__)


class OverwatchClientNotConfiguredError (Exception):
    pass


class OverwatchClientReportError (Exception):
    pass


class OverwatchClient:

    def __init__(self, report_url, report_token):
        self._session = None
        self._report_url = report_url
        self._report_token = report_token

    async def __aenter__(self):
        assert self._session is None
        # https://docs.python.org/3/reference/compound_stmts.html#the-async-with-statement
        self._session_manager = ClientSession()
        aenter = type(self._session_manager).__aenter__
        self._session = await aenter(self._session_manager)
        return self

    async def __aexit__(self, *args):
        aexit = type(self._session_manager).__aexit__
        await aexit(self._session_manager, *args)
        self._session = None
        self._session_manager = None

    async def send_report(self, report_data):
        assert isinstance(report_data, dict)
        if not self._report_url:
            raise OverwatchClientNotConfiguredError('No report_url')
        if self._session is None:
            raise Exception('Not in context block')
        post_kwargs = dict(
            json=report_data,
            headers={
                'Accept': 'application/json',
                'Authorization': 'token ' + self._report_token,
            },
            timeout=60)
        logger.debug('Sending Overwatch report - POST %s with payload: %s', self._report_url, smart_repr(report_data))
        try:
            async with self._session.post(self._report_url, **post_kwargs) as resp:
                logger.debug('Response: %r', resp)
                resp.raise_for_status()
        except Exception as e:
            raise OverwatchClientReportError('Failed to post report to {!r}: {!r}'.format(self._report_url, e))
