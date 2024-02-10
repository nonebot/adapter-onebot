import json
from pathlib import Path
from typing import Literal

import pytest
from nonebot.log import logger
from nonebot.compat import model_dump

from nonebot.adapters.onebot.v11.event import Sender
from nonebot.adapters.onebot.v11 import (
    Event,
    Adapter,
    MessageSegment,
    PrivateMessageEvent,
)


@pytest.mark.asyncio
async def test_event():
    with (Path(__file__).parent / "events.json").open("r") as f:
        test_events = json.load(f)

    for event_data in test_events:
        model_name: str = event_data.pop("_model")
        event = Adapter.json_to_event(event_data)
        assert model_name == event.__class__.__name__

    class MessageSelfEvent(Event):
        post_type: Literal["message_self"]

    event = MessageSelfEvent(self_id=0, time=0, post_type="message_self")

    Adapter.add_custom_model(MessageSelfEvent)
    parsed = Adapter.json_to_event(model_dump(event))
    assert parsed == event


@pytest.mark.asyncio
async def test_event_log():
    msg = (
        MessageSegment.text("[text]")
        + MessageSegment.at(123)
        + MessageSegment.text("<t\nag>")
    )
    event = PrivateMessageEvent(
        time=0,
        self_id=0,
        post_type="message",
        sub_type="friend",
        user_id=1,
        message_type="private",
        message_id=1,
        message=msg,
        original_message=msg,
        raw_message=str(msg),
        font=0,
        sender=Sender(),
        to_me=True,
    )
    logger.opt(colors=True).success(
        f"{event.get_event_name()}: {event.get_event_description()}"
    )
