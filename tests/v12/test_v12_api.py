import pytest

import nonebot
from nonebot.adapters.onebot.v12 import Adapter, BadRequest, ActionFailedWithRetcode


@pytest.mark.asyncio
async def test_api_result_handle():
    adapter = nonebot.get_adapter(Adapter)

    result = adapter._handle_api_result(
        {"status": "ok", "retcode": 0, "data": "test response", "message": ""}
    )
    assert result == "test response"

    with pytest.raises(BadRequest):
        adapter._handle_api_result(
            {
                "status": "failed",
                "retcode": 10001,
                "data": "",
                "message": "test message",
            }
        )

    class CustomFailed(ActionFailedWithRetcode):
        __retcode__ = ("61",)

    Adapter.add_custom_exception(CustomFailed)

    with pytest.raises(CustomFailed):
        adapter._handle_api_result(
            {
                "status": "failed",
                "retcode": 61525,
                "data": "",
                "message": "test message",
            }
        )
