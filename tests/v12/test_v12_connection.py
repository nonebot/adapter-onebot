import json
from pathlib import Path

import pytest
from nonebug import App


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoints", ["/onebot/v12/", "/onebot/v12/http", "/onebot/v12/http/"]
)
async def test_http(app: App, init_adapter, endpoints: str):
    import nonebot

    with (Path(__file__).parent / "events.json").open("r") as f:
        test_events = json.load(f)

    async with app.test_server() as ctx:
        client = ctx.get_client()
        event = test_events[0]
        model = event.pop("_model")
        headers = {
            "X-OneBot-Version": "12",
            "X-Impl": "test",
            "X-Platform": "test",
            "X-Self-ID": "0",
        }
        resp = await client.post(endpoints, json=event, headers=headers)
        assert resp.status_code == 204
        bots = nonebot.get_bots()
        assert "0" in bots


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoints", ["/onebot/v12/", "/onebot/v12/ws", "/onebot/v12/ws/"]
)
async def test_ws(app: App, init_adapter, endpoints: str):
    import nonebot

    async with app.test_server() as ctx:
        client = ctx.get_client()
        headers = {
            "X-OneBot-Version": "12",
            "X-Impl": "test",
            "X-Platform": "test",
            "X-Self-ID": "0",
        }
        async with client.websocket_connect(endpoints, headers=headers) as ws:
            bots = nonebot.get_bots()
            assert "0" in bots
