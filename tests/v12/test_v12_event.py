import json
from pathlib import Path
from typing import Literal
from datetime import datetime

import pytest
from nonebug import App
from pydantic import BaseModel


@pytest.mark.asyncio
async def test_event(app: App, init_adapter):
    from nonebot.adapters.onebot.v12 import Adapter

    with (Path(__file__).parent / "events.json").open("r") as f:
        test_events = json.load(f)

    for event_data in test_events:
        model_name: str = event_data.pop("_model")
        event = Adapter.json_to_event(event_data)
        assert model_name == event.__class__.__name__


@pytest.mark.asyncio
async def test_custom_model(app: App, init_adapter):
    from nonebot.adapters.onebot.v12 import Event, Adapter, MessageEvent

    class QQExtended(BaseModel):
        key: str

    class MessageSelfEvent(MessageEvent):
        detail_type: Literal["self"]
        qq: QQExtended

    class PlatformEvent(Event):
        impl: Literal["test"]
        platform: Literal["test"]

    event = {
        "id": "0",
        "impl": "test",
        "platform": "test",
        "self_id": "0",
        "time": datetime.now(),
        "type": "message",
        "detail_type": "self",
        "sub_type": "",
        "message_id": "0",
        "message": [{"type": "text", "data": {"text": "test"}}],
        "alt_message": "test",
        "user_id": "0",
        "qq.key": "value",
    }

    Adapter.add_custom_model(MessageSelfEvent)
    assert list(Adapter.get_event_model(event)) == [
        MessageSelfEvent,
        MessageEvent,
        Event,
    ]
    parsed = Adapter.json_to_event(event)
    assert isinstance(parsed, MessageSelfEvent)

    Adapter.add_custom_model(PlatformEvent, impl="test", platform="test")
    assert list(Adapter.get_event_model(event)) == [
        PlatformEvent,
        MessageSelfEvent,
        MessageEvent,
        Event,
    ]
    parsed = Adapter.json_to_event(event)
    assert isinstance(parsed, PlatformEvent)
