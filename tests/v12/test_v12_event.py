import json
from pathlib import Path
from datetime import datetime
from typing_extensions import Literal

import pytest


@pytest.mark.asyncio
async def test_event(init_adapter):
    from nonebot.adapters.onebot.v12 import Event, Adapter, PrivateMessageEvent

    with (Path(__file__).parent / "events.json").open("r") as f:
        test_events = json.load(f)

    for event_data in test_events:
        model_name: str = event_data.pop("_model")
        event = Adapter.json_to_event(event_data)
        assert model_name == event.__class__.__name__

    class MessageSelfEvent(Event):
        type: Literal["message_self"]

    event = MessageSelfEvent(
        id="0",
        impl="test",
        platform="test",
        self_id="0",
        time=datetime.now(),
        type="message_self",
        detail_type="",
        sub_type="",
    )

    Adapter.add_custom_model(MessageSelfEvent)
    parsed = Adapter.json_to_event(event.dict())
    assert parsed == event
