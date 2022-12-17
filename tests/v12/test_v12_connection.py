import json
import asyncio
from pathlib import Path

import pytest
from nonebug import App


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoints", ["/onebot/v12/", "/onebot/v12/http", "/onebot/v12/http/"]
)
async def test_http(app: App, init_adapter, endpoints: str):
    import nonebot

    with (Path(__file__).parent / "events.json").open("r", encoding="utf8") as f:
        test_events = json.load(f)

    async with app.test_server() as ctx:
        client = ctx.get_client()
        event = test_events[0]
        headers = {
            "X-OneBot-Version": "12",
            "X-Impl": "test",
        }
        resp = await client.post(endpoints, json=event, headers=headers)
        assert resp.status_code == 204
        bots = nonebot.get_bots()
        assert "0" in bots
        assert "2345678" not in bots

        event = test_events[1]
        resp = await client.post(endpoints, json=event, headers=headers)
        assert resp.status_code == 204
        assert "0" not in bots
        assert "2345678" in bots


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoints", ["/onebot/v12/", "/onebot/v12/ws", "/onebot/v12/ws/"]
)
async def test_ws(app: App, init_adapter, endpoints: str):
    import nonebot

    with (Path(__file__).parent / "events.json").open("r", encoding="utf8") as f:
        test_events = json.load(f)

    async with app.test_server() as ctx:
        client = ctx.get_client()
        headers = {
            "Sec-WebSocket-Protocol": "12.test",
        }
        async with client.websocket_connect(endpoints, headers=headers) as ws:
            await ws.send_json(test_events[0])
            await asyncio.sleep(0)
            bots = nonebot.get_bots()
            assert "0" in bots
            assert "2345678" not in bots

            await ws.send_json(test_events[1])
            await asyncio.sleep(0)
            assert "0" not in bots
            assert "2345678" in bots
