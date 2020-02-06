from pytest import mark

from nginx_log_monitor.clients import OverwatchClient


@mark.asyncio
async def test_overwatch_client_context_manager():
    async with OverwatchClient(report_url='https://example.com/', report_token='foo') as client:
        pass
