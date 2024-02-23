import json
import asyncio
from pathlib import Path

import pytest
from nonebug import App

import nonebot
from nonebot.adapters.onebot.v11 import Adapter


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoints", ["/onebot/v11/", "/onebot/v11/http", "/onebot/v11/http/"]
)
async def test_http(app: App, endpoints: str):
    with (Path(__file__).parent / "events.json").open("r") as f:
        test_events = json.load(f)

    adapter = nonebot.get_adapter(Adapter)

    async with app.test_server() as ctx:
        client = ctx.get_client()
        event = test_events[0]
        event.pop("_model")
        headers = {"X-Self-ID": "0", "Authorization": "Bearer test1"}
        resp = await client.post(endpoints, json=event, headers=headers)
        assert resp.status_code == 204
        bots = nonebot.get_bots()
        assert "0" in bots
        assert "0" in adapter.bots
        adapter.bot_disconnect(bots["0"])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoints", ["/onebot/v11/", "/onebot/v11/ws", "/onebot/v11/ws/"]
)
async def test_ws(app: App, endpoints: str):
    adapter = nonebot.get_adapter(Adapter)

    async with app.test_server() as ctx:
        client = ctx.get_client()
        headers = {"X-Self-ID": "0", "Authorization": "Bearer test1"}
        async with client.websocket_connect(endpoints, headers=headers) as ws:
            assert "0" in nonebot.get_bots()
            assert "0" in adapter.bots
            await ws.close()

        await asyncio.sleep(1)
        assert "0" not in nonebot.get_bots()
        assert "0" not in adapter.bots
