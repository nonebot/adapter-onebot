import re
from enum import IntEnum, auto
from asyncio import get_running_loop
from typing import Set, List, Union, Optional

from nonebot.matcher import Matcher
from nonebot.params import Depends, EventMessage

from .message import Message
from .event import MessageEvent, GroupMessageEvent


def extract_image_urls(message: Message) -> List[str]:
    return [
        segment.data["url"]
        for segment in message
        if (segment.type == "image") and ("url" in segment.data)
    ]


def ImageURLs(prompt: Optional[str] = None) -> List[str]:
    async def dependency(
        matcher: Matcher, message: Message = EventMessage()
    ) -> List[str]:
        urls = extract_image_urls(message)
        if not urls and prompt:
            await matcher.finish(prompt)
        return urls

    return Depends(dependency)


NUMBERS_REGEXP = re.compile(r"[+-]?(\d*\.?\d+|\d+\.?\d*)")


def extract_numbers(message: Message) -> List[float]:
    return [
        float(matched)
        for matched in NUMBERS_REGEXP.findall(message.extract_plain_text())
    ]


def Numbers(prompt: Optional[str] = None) -> List[float]:
    async def dependency(
        matcher: Matcher, message: Message = EventMessage()
    ) -> List[float]:
        numbers = extract_numbers(message)
        if not numbers and prompt:
            await matcher.finish(prompt)
        return numbers

    return Depends(dependency)


CHINESE_AGREE_WORD = {
    "要",
    "用",
    "是",
    "好",
    "对",
    "嗯",
    "行",
    "ok",
    "okay",
    "yeah",
    "yep",
    "当真",
    "当然",
    "必须",
    "可以",
    "肯定",
    "没错",
    "确定",
    "确认",
}
CHINESE_DECLINE_WORD = {
    "不",
    "不要",
    "不用",
    "不是",
    "否",
    "不好",
    "不对",
    "不行",
    "别",
    "no",
    "nono",
    "nonono",
    "nope",
    "不ok",
    "不可以",
    "不能",
    "不可以",
}
CHINESE_TRAILING_WORD = ",.!?~，。！？～了的呢吧呀啊呗啦"


def convert_chinese_to_bool(message: Union[Message, str]) -> Optional[bool]:
    text = message.extract_plain_text() if isinstance(message, Message) else message
    text = text.lower().strip().replace(" ", "").rstrip(CHINESE_TRAILING_WORD)

    if text in CHINESE_AGREE_WORD:
        return True
    if text in CHINESE_DECLINE_WORD:
        return False
    return None


def remove_empty_lines(
    message: Union[Message, str], include_stripped: bool = False
) -> str:
    text = message.extract_plain_text() if isinstance(message, Message) else message
    return "".join(
        line
        for line in text.splitlines(keepends=False)
        if bool(line.strip() if include_stripped else line)
    )


CHINESE_CANCELLATION_WORDS = {"算", "别", "不", "停", "取消"}
CHINESE_CANCELLATION_REGEX_1 = re.compile(r"^那?[算别不停]\w{0,3}了?吧?$")
CHINESE_CANCELLATION_REGEX_2 = re.compile(r"^那?(?:[给帮]我)?取消了?吧?$")


def is_cancellation(message: Union[Message, str]) -> bool:
    text = message.extract_plain_text() if isinstance(message, Message) else message
    return any(kw in text for kw in CHINESE_CANCELLATION_WORDS) and bool(
        CHINESE_CANCELLATION_REGEX_1.match(text)
        or CHINESE_CANCELLATION_REGEX_2.match(text)
    )


def HandleCancellation(cancel_prompt: Optional[str] = None) -> bool:
    async def dependency(matcher: Matcher, message: Message = EventMessage()) -> bool:
        cancelled = is_cancellation(message)
        if cancelled and cancel_prompt:
            await matcher.finish(cancel_prompt)
        return not cancelled

    return Depends(dependency)


class CooldownIsolateLevel(IntEnum):
    GLOBAL = auto()
    GROUP = auto()
    USER = auto()
    GROUP_USER = auto()


def Cooldown(
    cooldown: float = 5,
    *,
    prompt: Optional[str] = None,
    isolate_level: CooldownIsolateLevel = CooldownIsolateLevel.USER,
) -> None:
    if not isinstance(isolate_level, CooldownIsolateLevel):
        raise ValueError(
            f"invalid isolate level: {isolate_level!r}, "
            "isolate level must use provided enumerate value."
        )
    debounced: Set[str] = set()

    async def dependency(matcher: Matcher, event: MessageEvent):
        loop = get_running_loop()

        if isolate_level is CooldownIsolateLevel.GROUP:
            key = str(
                event.group_id
                if isinstance(event, GroupMessageEvent)
                else event.user_id,
            )
        elif isolate_level is CooldownIsolateLevel.USER:
            key = str(event.user_id)
        elif isolate_level is CooldownIsolateLevel.GROUP_USER:
            key = (
                f"{event.group_id}_{event.user_id}"
                if isinstance(event, GroupMessageEvent)
                else str(event.user_id)
            )
        else:
            key = CooldownIsolateLevel.GLOBAL.name

        if key in debounced:
            await matcher.finish(prompt)
        else:
            debounced.add(key)
            loop.call_later(cooldown, lambda: debounced.remove(key))
        return

    return Depends(dependency)
