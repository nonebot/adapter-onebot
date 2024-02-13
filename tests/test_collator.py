from typing import Literal

import pytest

from nonebot.adapters import Event
from nonebot.adapters.onebot.collator import SEPARATOR, Collator


@pytest.mark.asyncio
async def test_collator_simple_build():
    class TestModel(Event):
        type: str
        detail_type: str

    class MessageModel(TestModel):
        type: Literal["message"]

    class PrivateModel(MessageModel):
        detail_type: Literal["private"]

    collator = Collator(
        "test", [TestModel, MessageModel, PrivateModel], ("type", "detail_type")
    )
    tree = collator.tree
    assert tree[""] == TestModel
    assert tree[f"{SEPARATOR}message"] == MessageModel
    assert tree[f"{SEPARATOR}message{SEPARATOR}private"] == PrivateModel


@pytest.mark.asyncio
async def test_collator_peer_build():
    class TestModel(Event):
        type: str

    class MessageModel(TestModel):
        type: Literal["message"]
        message_type: str

    class PrivateModel(MessageModel):
        message_type: Literal["private"]

    class NoticeModel(TestModel):
        type: Literal["notice"]
        request_type: str

    class IncreaseModel(NoticeModel):
        request_type: Literal["increase"]

    collator = Collator(
        "test",
        [TestModel, MessageModel, PrivateModel, NoticeModel, IncreaseModel],
        ("type", ("message_type", "request_type")),
    )
    tree = collator.tree
    assert tree[""] == TestModel
    assert tree[f"{SEPARATOR}message"] == MessageModel
    assert tree[f"{SEPARATOR}message{SEPARATOR}private"] == PrivateModel
    assert tree[f"{SEPARATOR}notice"] == NoticeModel
    assert tree[f"{SEPARATOR}notice{SEPARATOR}increase"] == IncreaseModel


@pytest.mark.asyncio
async def test_collator_get_model():
    class TestModel(Event):
        type: str
        detail_type: str

    class MessageModel(TestModel):
        type: Literal["message"]

    class PrivateModel(MessageModel):
        detail_type: Literal["private"]

    collator = Collator(
        "test", [TestModel, MessageModel, PrivateModel], ("type", "detail_type")
    )

    models = collator.get_model({"type": "not_exists"})
    assert models == [TestModel]

    models = collator.get_model({"type": "message", "detail_type": "private"})
    assert models == [PrivateModel, MessageModel, TestModel]

    models = collator.get_model({"type": "message", "detail_type": "not_exists"})
    assert models == [MessageModel, TestModel]
