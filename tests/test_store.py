import asyncio

import pytest

from nonebot.adapters.onebot.store import ResultStore


@pytest.mark.asyncio
async def test_store():
    store = ResultStore()

    seq = store.get_seq()
    data = {"test": "test"}
    response_data = {
        "status": "success",
        "retcode": 0,
        "data": data,
        "echo": str(seq),
    }

    async def feed_result():
        store.add_result(response_data)

    task = asyncio.create_task(feed_result())
    resp = await store.fetch(seq, 10.0)
    await task
    assert resp == response_data
