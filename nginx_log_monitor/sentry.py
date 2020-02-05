async def report_to_sentry(conf, access_log_queue):
    while True:
        access_log_record = await access_log_queue.get()

