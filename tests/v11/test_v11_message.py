import pytest


@pytest.mark.asyncio
async def test_message_escape(init_adapter):
    from nonebot.adapters.onebot.v11 import Message, MessageSegment

    a = Message([MessageSegment.text("test"), MessageSegment.at(123)])
    assert Message(str(a)) == a

    assert Message() + "[CQ:test]" == Message(MessageSegment.text("[CQ:test]"))
    assert "[CQ:test]" + Message() == Message(MessageSegment.text("[CQ:test]"))

    a = Message()
    a += "[CQ:test]"
    assert a == Message(MessageSegment.text("[CQ:test]"))

    assert MessageSegment.text("test") + "[CQ:test]" == Message(
        [MessageSegment.text("test"), MessageSegment.text("[CQ:test]")]
    )
    assert "[CQ:test]" + MessageSegment.text("test") == Message(
        [MessageSegment.text("[CQ:test]"), MessageSegment.text("test")]
    )
