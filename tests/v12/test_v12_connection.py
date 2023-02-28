import json
import asyncio
from pathlib import Path

import pytest
from nonebug import App

import nonebot

with open(Path(__file__).parent / "events.json", "r", encoding="utf8") as f:
    test_events = json.load(f)
    CONNECTION_META_EVENT = test_events[0]
    QQ_ONLINE_EVENT = test_events[1]
    QQ_OFFLINE_EVENT = test_events[2]
    PRIVATE_MESSAGE_EVENT = test_events[3]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoints", ["/onebot/v12/", "/onebot/v12/http", "/onebot/v12/http/"]
)
async def test_http(app: App, endpoints: str):
    from nonebot.adapters.onebot.v12 import Adapter

    adapter = nonebot.get_adapter(Adapter)

    async with app.test_server() as ctx:
        client = ctx.get_client()
        headers = {
            "X-OneBot-Version": "12",
            "X-Impl": "test",
            "Authorization": "Bearer test",
        }
        resp = await client.post(endpoints, json=PRIVATE_MESSAGE_EVENT, headers=headers)
        assert resp.status_code == 204
        bots = nonebot.get_bots()
        assert "0" in bots
        assert "0" in adapter.bots
        assert "2345678" not in bots

        resp = await client.post(endpoints, json=QQ_OFFLINE_EVENT, headers=headers)
        assert resp.status_code == 204
        bots = nonebot.get_bots()
        assert "0" not in bots
        assert "2345678" in bots
        assert "2345678" in adapter.bots

        adapter.bot_disconnect(bots["2345678"])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoints", ["/onebot/v12/", "/onebot/v12/ws", "/onebot/v12/ws/"]
)
async def test_ws(app: App, endpoints: str):
    from nonebot.adapters.onebot.v12 import Adapter

    adapter = nonebot.get_adapter(Adapter)

    async with app.test_server() as ctx:
        client = ctx.get_client()
        headers = {
            "Sec-WebSocket-Protocol": "12.test",
            "Authorization": "Bearer test",
        }
        async with client.websocket_connect(endpoints, headers=headers) as ws:
            await ws.send_json(CONNECTION_META_EVENT)

            await ws.send_json(PRIVATE_MESSAGE_EVENT)
            await asyncio.sleep(0)
            bots = nonebot.get_bots()
            assert "0" in bots
            assert "2345678" not in bots

            await ws.send_json(QQ_OFFLINE_EVENT)
            await asyncio.sleep(0)
            bots = nonebot.get_bots()
            assert "0" not in bots
            assert "2345678" in bots

        assert "2345678" not in nonebot.get_bots()
        assert "2345678" not in adapter.bots


async def test_ws_missing_connect_meta_event(app: App):
    endpoints = "/onebot/v12/"

    async with app.test_server() as ctx:
        client = ctx.get_client()
        headers = {
            "Sec-WebSocket-Protocol": "12.test",
            "Authorization": "Bearer test",
        }
        async with client.websocket_connect(endpoints, headers=headers) as ws:
            await ws.send_json(PRIVATE_MESSAGE_EVENT)
            with pytest.raises(Exception) as e:
                await ws.receive_json()
            assert e.value.args[0] == {
                "type": "websocket.close",
                "code": 1008,
                "reason": "Missing connect meta event",
            }


async def test_ws_duplicate_bot(app: App):
    """测试连接两个相同 id 但协议不同的 bot"""
    from nonebot.adapters.onebot.v11 import Adapter

    adapter = nonebot.get_adapter(Adapter)

    # 先连接一个 v11 bot
    endpoints = "/onebot/v11/"

    async with app.test_server() as ctx:
        client = ctx.get_client()
        headers = {"X-Self-ID": "0"}
        with (Path(__file__).parent.parent / "v11" / "events.json").open(
            "r", encoding="utf8"
        ) as f:
            event = json.load(f)[0]
        resp = await client.post(endpoints, json=event, headers=headers)
        assert resp.status_code == 204
        assert "0" in nonebot.get_bots()

    # 再连接一个 v12 bot
    endpoints = "/onebot/v12/"

    async with app.test_server() as ctx:
        client = ctx.get_client()
        headers = {
            "Sec-WebSocket-Protocol": "12.test",
            "Authorization": "Bearer test",
        }

        async with client.websocket_connect(endpoints, headers=headers) as ws:
            await ws.send_json(CONNECTION_META_EVENT)
            await ws.send_json(PRIVATE_MESSAGE_EVENT)

            with pytest.raises(Exception) as e:
                await ws.receive_json()
            assert e.value.args[0] == {
                "type": "websocket.close",
                "code": 1000,
                "reason": "",
            }

        async with client.websocket_connect(endpoints, headers=headers) as ws:
            await ws.send_json(CONNECTION_META_EVENT)
            await ws.send_json(QQ_ONLINE_EVENT)

            with pytest.raises(Exception) as e:
                await asyncio.wait_for(ws.receive_json(), 5)
            assert e.value.args[0] == {
                "type": "websocket.close",
                "code": 1000,
                "reason": "",
            }

    adapter.bot_disconnect(nonebot.get_bot("0"))


async def test_http_auth_missing(app: App):
    endpoints = "/onebot/v12/"

    async with app.test_server() as ctx:
        client = ctx.get_client()
        headers = {
            "X-OneBot-Version": "12",
            "X-Impl": "test",
        }
        resp = await client.post(endpoints, json=PRIVATE_MESSAGE_EVENT, headers=headers)
        assert resp.status_code == 403


async def test_http_auth_header(app: App):
    from nonebot.adapters.onebot.v12 import Adapter

    adapter = nonebot.get_adapter(Adapter)

    endpoints = "/onebot/v12/"

    async with app.test_server() as ctx:
        client = ctx.get_client()
        headers = {
            "X-OneBot-Version": "12",
            "X-Impl": "test",
            "Authorization": "Bearer test",
        }
        resp = await client.post(endpoints, json=PRIVATE_MESSAGE_EVENT, headers=headers)
        assert resp.status_code == 204
        bots = nonebot.get_bots()
        assert "0" in bots
        assert "2345678" not in bots

        adapter.bot_disconnect(nonebot.get_bot("0"))


async def test_http_auth_query(app: App):
    from nonebot.adapters.onebot.v12 import Adapter

    adapter = nonebot.get_adapter(Adapter)

    endpoints = "/onebot/v12/?access_token=test"

    async with app.test_server() as ctx:
        client = ctx.get_client()
        headers = {
            "X-OneBot-Version": "12",
            "X-Impl": "test",
        }
        resp = await client.post(endpoints, json=PRIVATE_MESSAGE_EVENT, headers=headers)
        assert resp.status_code == 204
        bots = nonebot.get_bots()
        assert "0" in bots
        assert "2345678" not in bots

        adapter.bot_disconnect(nonebot.get_bot("0"))


async def test_ws_auth_missing(app: App):
    endpoints = "/onebot/v12/"

    async with app.test_server() as ctx:
        client = ctx.get_client()
        headers = {
            "Sec-WebSocket-Protocol": "12.test",
        }
        with pytest.raises(AssertionError):
            async with client.websocket_connect(endpoints, headers=headers) as ws:
                await ws.send_json(CONNECTION_META_EVENT)
                await asyncio.sleep(0)


async def test_ws_auth_header(app: App):
    endpoints = "/onebot/v12/"

    async with app.test_server() as ctx:
        client = ctx.get_client()
        headers = {
            "Sec-WebSocket-Protocol": "12.test",
            "Authorization": "Bearer test",
        }
        async with client.websocket_connect(endpoints, headers=headers) as ws:
            await ws.send_json(CONNECTION_META_EVENT)

            await ws.send_json(PRIVATE_MESSAGE_EVENT)
            await asyncio.sleep(0)
            bots = nonebot.get_bots()
            assert "0" in bots
            assert "2345678" not in bots

        assert "0" not in nonebot.get_bots()


async def test_ws_auth_query(app: App):
    endpoints = "/onebot/v12/?access_token=test"

    async with app.test_server() as ctx:
        client = ctx.get_client()
        headers = {
            "Sec-WebSocket-Protocol": "12.test",
        }
        async with client.websocket_connect(endpoints, headers=headers) as ws:
            await ws.send_json(CONNECTION_META_EVENT)

            await ws.send_json(PRIVATE_MESSAGE_EVENT)
            await asyncio.sleep(0)
            bots = nonebot.get_bots()
            assert "0" in bots
            assert "2345678" not in bots

        assert "0" not in nonebot.get_bots()
