import pytest

from nonebot.adapters.onebot.v11 import Message, MessageSegment


@pytest.mark.asyncio
async def test_message_escape():
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


@pytest.mark.asyncio
async def test_message_rich_expr():
    a = MessageSegment.text("[test],test")
    assert a.to_rich_text() == "&#91;test&#93;,test"
    b = MessageSegment.at(123)
    assert b.to_rich_text() == "[at:qq=123]"
