import asyncio

import pytest
from nonebug import App


@pytest.mark.asyncio
async def test_api_reply(app: App, init_adapter):
    from nonebot.adapters.onebot.v11 import Adapter
    from nonebot.adapters.onebot.store import ResultStore

    result_store = ResultStore()

    self_id = "test"
    seq = result_store.get_seq()
    data = {"test": "test"}
    response_data = {
        "status": "success",
        "retcode": 0,
        "data": data,
        "echo": {
            "seq": seq,
        },
    }

    async def feed_result():
        Adapter.json_to_event(response_data, self_id)

    asyncio.create_task(feed_result())
    resp = await result_store.fetch(self_id, seq, 10.0)
    assert resp == response_data
