import pytest
from nonebug import App


@pytest.mark.asyncio
async def test_api_result_handle(app: App, init_adapter):
    from nonebot import get_driver
    from nonebot.adapters.onebot.v12 import Adapter, BadRequest, ActionFailedWithRetcode

    adapter: Adapter = get_driver()._adapters[Adapter.get_name()]  # type: ignore

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
