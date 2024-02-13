import pytest

from nonebot.adapters.onebot.v12 import MessageSegment


@pytest.mark.asyncio
async def test_message_rich_expr():
    a = MessageSegment.text("[test],test")
    assert a.to_rich_text() == "&#91;test&#93;,test"
    b = MessageSegment.mention("123")
    assert b.to_rich_text() == "[mention:user_id=123]"
