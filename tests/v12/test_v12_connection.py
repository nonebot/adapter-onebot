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


@pytest.mark.parametrize(
    "nonebug_init",
    [pytest.param({"onebot_v12_access_token": "test"}, id="access_token")],
    indirect=True,
)
async def test_http_auth_missing(app: App, init_adapter):
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


@pytest.mark.parametrize(
    "nonebug_init",
    [pytest.param({"onebot_v12_access_token": "test"}, id="access_token")],
    indirect=True,
)
async def test_http_auth_header(app: App, init_adapter):
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


@pytest.mark.parametrize(
    "nonebug_init",
    [pytest.param({"onebot_v12_access_token": "test"}, id="access_token")],
    indirect=True,
)
async def test_http_auth_query(app: App, init_adapter):
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


@pytest.mark.parametrize(
    "nonebug_init",
    [pytest.param({"onebot_v12_access_token": "test"}, id="access_token")],
    indirect=True,
)
async def test_ws_auth_missing(app: App, init_adapter):
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
                await ws.send_json(test_events[0])
                await asyncio.sleep(0)


@pytest.mark.parametrize(
    "nonebug_init",
    [pytest.param({"onebot_v12_access_token": "test"}, id="access_token")],
    indirect=True,
)
async def test_ws_auth_header(app: App, init_adapter):
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
            await ws.send_json(test_events[0])
            await asyncio.sleep(0)
            bots = nonebot.get_bots()
            assert "0" in bots
            assert "2345678" not in bots


@pytest.mark.parametrize(
    "nonebug_init",
    [pytest.param({"onebot_v12_access_token": "test"}, id="access_token")],
    indirect=True,
)
async def test_ws_auth_query(app: App, init_adapter):
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
            await ws.send_json(test_events[0])
            await asyncio.sleep(0)
            bots = nonebot.get_bots()
            assert "0" in bots
            assert "2345678" not in bots
