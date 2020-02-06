from logging import getLogger

try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None


logger = getLogger(__name__)


class SentryClient:

    def __init__(self):
        self._clients_by_dsn = {}

    def _get_client(self, dsn):
        client = self._clients_by_dsn.get(dsn)
        if client is None:
            if sentry_sdk is None:
                raise Exception('sentry_sdk not installed')
            client = sentry_sdk.Client(dsn)
            self._clients_by_dsn[dsn] = client
        return client

    async def report(self, dsn, event):
        client = self._get_client(dsn)
        event_id = client.capture_event(event)
        if event_id:
            logger.info('Sentry event id: %s', event_id)
        else:
            logger.warning('Event discarded')
