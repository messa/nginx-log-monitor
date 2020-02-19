from aiohttp import ClientSession
from logging import getLogger
from reprlib import repr as smart_repr


logger = getLogger(__name__)

post_timeout_s = 30


class OverwatchClientNotConfiguredError (Exception):
    pass


class OverwatchClientReportError (Exception):
    pass


class OverwatchClient:

    def __init__(self, client_session, report_url, report_token):
        self._session = client_session
        self._report_url = report_url
        self._report_token = report_token

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
            timeout=post_timeout_s)
        logger.debug('Sending Overwatch report - POST %s with payload: %s', self._report_url, smart_repr(report_data))
        try:
            async with self._session.post(self._report_url, **post_kwargs) as resp:
                logger.debug('Response: %r', resp)
                resp.raise_for_status()
        except Exception as e:
            raise OverwatchClientReportError('Failed to post report to {!r}: {!r}'.format(self._report_url, e))
