import json
import asyncio
from pathlib import Path

import pytest
from nonebug import App


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoints", ["/onebot/v12/", "/onebot/v12/http", "/onebot/v12/http/"]
)
async def test_http(app: App, endpoints: str):
    import nonebot

    with (Path(__file__).parent / "events.json").open("r", encoding="utf8") as f:
        test_events = json.load(f)

    async with app.test_server() as ctx:
        client = ctx.get_client()
        event = test_events[0]
        headers = {
            "X-OneBot-Version": "12",
            "X-Impl": "test",
            "Authorization": "Bearer test",
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
async def test_ws(app: App, endpoints: str):
    import nonebot

    with (Path(__file__).parent / "events.json").open("r", encoding="utf8") as f:
        test_events = json.load(f)

    async with app.test_server() as ctx:
        client = ctx.get_client()
        headers = {
            "Sec-WebSocket-Protocol": "12.test",
            "Authorization": "Bearer test",
        }
        async with client.websocket_connect(endpoints, headers=headers) as ws:
            await ws.send_json(test_events[2])

            await ws.send_json(test_events[0])
            await asyncio.sleep(0)
            bots = nonebot.get_bots()
            assert "0" in bots
            assert "2345678" not in bots

            await ws.send_json(test_events[1])
            await asyncio.sleep(0)
            assert "0" not in bots
            assert "2345678" in bots


async def test_ws_missing_connect_meta_event(app: App):
    endpoints = "/onebot/v12/"

    with (Path(__file__).parent / "events.json").open("r", encoding="utf8") as f:
        test_events = json.load(f)

    async with app.test_server() as ctx:
        client = ctx.get_client()
        headers = {
            "Sec-WebSocket-Protocol": "12.test",
            "Authorization": "Bearer test",
        }
        async with client.websocket_connect(endpoints, headers=headers) as ws:
            await ws.send_json(test_events[0])
            with pytest.raises(Exception) as e:
                await ws.receive_json()
            assert e.value.args[0] == {
                "type": "websocket.close",
                "code": 1008,
                "reason": "Missing connect meta event",
            }


async def test_ws_duplicate_bot(app: App):
    """测试连接两个相同 id 但协议不同的 bot"""
    import nonebot

    # 先连接一个 v11 bot
    endpoints = "/onebot/v11/"

    with (Path(__file__).parent.parent / "v11" / "events.json").open(
        "r", encoding="utf8"
    ) as f:
        test_events = json.load(f)

    async with app.test_server() as ctx:
        client = ctx.get_client()
        event = test_events[0]
        headers = {"X-Self-ID": "0"}
        resp = await client.post(endpoints, json=event, headers=headers)
        assert resp.status_code == 204
        bots = nonebot.get_bots()
        assert "0" in bots

    # 再连接一个 v12 bot
    endpoints = "/onebot/v12/"

    with (Path(__file__).parent / "events.json").open("r", encoding="utf8") as f:
        test_events = json.load(f)

    async with app.test_server() as ctx:
        client = ctx.get_client()
        headers = {
            "Sec-WebSocket-Protocol": "12.test",
            "Authorization": "Bearer test",
        }
        async with client.websocket_connect(endpoints, headers=headers) as ws:
            await ws.send_json(test_events[2])
            await ws.send_json(test_events[0])

            with pytest.raises(Exception) as e:
                await asyncio.wait_for(ws.receive_json(), 5)
            assert e.value.args[0] == {
                "type": "websocket.close",
                "code": 1000,
                "reason": "",
            }

        # 再次尝试依旧会报错，而不会因为 bot 被错误移除而正常连接
        async with client.websocket_connect(endpoints, headers=headers) as ws:
            await ws.send_json(test_events[2])
            await ws.send_json(test_events[0])

            # 如果第二次是 TimeoutError，说明 bot 被移除了，这个测试会报错
            with pytest.raises(Exception) as e:
                await asyncio.wait_for(ws.receive_json(), 5)
            assert e.value.args[0] == {
                "type": "websocket.close",
                "code": 1000,
                "reason": "",
            }

        # 重复两次 StatusUpdateMetaEvent 也不应报错
        async with client.websocket_connect(endpoints, headers=headers) as ws:
            await ws.send_json(test_events[2])
            await ws.send_json(test_events[3])

            with pytest.raises(Exception) as e:
                await asyncio.wait_for(ws.receive_json(), 5)
            assert e.value.args[0] == {
                "type": "websocket.close",
                "code": 1000,
                "reason": "",
            }

        async with client.websocket_connect(endpoints, headers=headers) as ws:
            await ws.send_json(test_events[2])
            await ws.send_json(test_events[3])

            # 如果第二次是 TimeoutError，说明 bot 被移除了，这个测试会报错
            with pytest.raises(Exception) as e:
                await asyncio.wait_for(ws.receive_json(), 5)
            assert e.value.args[0] == {
                "type": "websocket.close",
                "code": 1000,
                "reason": "",
            }


async def test_http_auth_missing(app: App):
    endpoints = "/onebot/v12/"

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
        assert resp.status_code == 403


async def test_http_auth_header(app: App):
    import nonebot

    endpoints = "/onebot/v12/"

    with (Path(__file__).parent / "events.json").open("r", encoding="utf8") as f:
        test_events = json.load(f)

    async with app.test_server() as ctx:
        client = ctx.get_client()
        event = test_events[0]
        headers = {
            "X-OneBot-Version": "12",
            "X-Impl": "test",
            "Authorization": "Bearer test",
        }
        resp = await client.post(endpoints, json=event, headers=headers)
        assert resp.status_code == 204
        bots = nonebot.get_bots()
        assert "0" in bots
        assert "2345678" not in bots


async def test_http_auth_query(app: App):
    import nonebot

    endpoints = "/onebot/v12/?access_token=test"

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


async def test_ws_auth_missing(app: App):
    endpoints = "/onebot/v12/"

    with (Path(__file__).parent / "events.json").open("r", encoding="utf8") as f:
        test_events = json.load(f)

    async with app.test_server() as ctx:
        client = ctx.get_client()
        headers = {
            "Sec-WebSocket-Protocol": "12.test",
        }
        with pytest.raises(AssertionError):
            async with client.websocket_connect(endpoints, headers=headers) as ws:
                await ws.send_json(test_events[2])
                await asyncio.sleep(0)


async def test_ws_auth_header(app: App):
    import nonebot

    endpoints = "/onebot/v12/"

    with (Path(__file__).parent / "events.json").open("r", encoding="utf8") as f:
        test_events = json.load(f)

    async with app.test_server() as ctx:
        client = ctx.get_client()
        headers = {
            "Sec-WebSocket-Protocol": "12.test",
            "Authorization": "Bearer test",
        }
        async with client.websocket_connect(endpoints, headers=headers) as ws:
            await ws.send_json(test_events[2])

            await ws.send_json(test_events[0])
            await asyncio.sleep(0)
            bots = nonebot.get_bots()
            assert "0" in bots
            assert "2345678" not in bots


async def test_ws_auth_query(app: App):
    import nonebot

    endpoints = "/onebot/v12/?access_token=test"

    with (Path(__file__).parent / "events.json").open("r", encoding="utf8") as f:
        test_events = json.load(f)

    async with app.test_server() as ctx:
        client = ctx.get_client()
        headers = {
            "Sec-WebSocket-Protocol": "12.test",
        }
        async with client.websocket_connect(endpoints, headers=headers) as ws:
            await ws.send_json(test_events[2])

            await ws.send_json(test_events[0])
            await asyncio.sleep(0)
            bots = nonebot.get_bots()
            assert "0" in bots
            assert "2345678" not in bots
