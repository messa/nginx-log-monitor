from logging import getLogger


logger = getLogger(__name__)


async def report_to_sentry(conf, access_log_queue, sentry_client):
    while True:
        access_log_record = await access_log_queue.get()
        if access_log_record.status >= 500:
            await sentry_client.report(
                dsn=conf.sentry.dsn,
                event=str(access_log_record))
