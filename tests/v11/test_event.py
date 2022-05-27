import json
from pathlib import Path
from typing_extensions import Literal

import pytest
from nonebug import App


@pytest.mark.asyncio
async def test_event(app: App, init_adapter):
    from nonebot.adapters.onebot.v11 import Event, Adapter

    with (Path(__file__).parent / "events.json").open("r") as f:
        test_events = json.load(f)

    for event_data in test_events:
        model_name: str = event_data.pop("_model")
        event = Adapter.json_to_event(event_data)
        assert model_name == event.__class__.__name__

    class MessageSelfEvent(Event):
        __event__ = "message_self"
        post_type: Literal["message_self"]

    event = MessageSelfEvent(self_id=0, time=0, post_type="message_self")

    Adapter.add_custom_model(MessageSelfEvent)
    parsed = Adapter.json_to_event(event.dict())
    assert parsed == event
