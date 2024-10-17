import anyio
import pytest

from nonebot.adapters.onebot.store import ResultStore


@pytest.mark.anyio
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

    async with anyio.create_task_group() as tg:
        tg.start_soon(feed_result)
        with anyio.fail_after(10):
            resp = await tg.start(store.fetch, seq)

    assert resp == response_data
