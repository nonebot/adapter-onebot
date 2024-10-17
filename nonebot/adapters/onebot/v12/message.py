"""OneBot v12 消息类型。

FrontMatter:
    sidebar_position: 5
    description: onebot.v12.message 模块
"""

from functools import partial
from typing import Any, Optional
from collections.abc import Iterable
from typing_extensions import override

from nonebot.adapters import Message as BaseMessage
from nonebot.adapters.onebot.utils import rich_escape
from nonebot.adapters.onebot.utils import truncate as trunc
from nonebot.adapters import MessageSegment as BaseMessageSegment


class MessageSegment(BaseMessageSegment["Message"]):
    """OneBot v12 协议 MessageSegment 适配。具体方法参考协议消息段类型或源码。"""

    @classmethod
    @override
    def get_message_class(cls) -> type["Message"]:
        return Message

    @override
    def __str__(self) -> str:
        return self.to_rich_text(truncate=None)

    def to_rich_text(self, truncate: Optional[int] = 70) -> str:
        if self.is_text():
            return rich_escape(self.data.get("text", ""), escape_comma=False)

        truncate_func = partial(trunc, length=truncate) if truncate else lambda x: x

        params = ", ".join(
            f"{k}={rich_escape(truncate_func(str(v)))}"
            for k, v in self.data.items()
            if v is not None
        )
        return f"[{self.type}{':' if params else ''}{params}]"

    @override
    def is_text(self) -> bool:
        return self.type == "text"

    @staticmethod
    def text(text: str, **kwargs) -> "MessageSegment":
        return MessageSegment("text", {**kwargs, "text": text})

    @staticmethod
    def mention(user_id: str, **kwargs) -> "MessageSegment":
        return MessageSegment("mention", {**kwargs, "user_id": user_id})

    @staticmethod
    def mention_all(**kwargs) -> "MessageSegment":
        return MessageSegment("mention_all", {**kwargs})

    @staticmethod
    def image(file_id: str, **kwargs) -> "MessageSegment":
        return MessageSegment("image", {**kwargs, "file_id": file_id})

    @staticmethod
    def voice(file_id: str, **kwargs) -> "MessageSegment":
        return MessageSegment("voice", {**kwargs, "file_id": file_id})

    @staticmethod
    def audio(file_id: str, **kwargs) -> "MessageSegment":
        return MessageSegment("audio", {**kwargs, "file_id": file_id})

    @staticmethod
    def video(file_id: str, **kwargs) -> "MessageSegment":
        return MessageSegment("video", {**kwargs, "file_id": file_id})

    @staticmethod
    def file(file_id: str, **kwargs) -> "MessageSegment":
        return MessageSegment("file", {**kwargs, "file_id": file_id})

    @staticmethod
    def location(
        latitude: float,
        longitude: float,
        title: str,
        content: str,
        **kwargs,
    ) -> "MessageSegment":
        return MessageSegment(
            "location",
            {
                **kwargs,
                "latitude": latitude,
                "longitude": longitude,
                "title": title,
                "content": content,
            },
        )

    @staticmethod
    def reply(message_id: str, **kwargs: Any) -> "MessageSegment":
        return MessageSegment("reply", {**kwargs, "message_id": message_id})


class Message(BaseMessage[MessageSegment]):
    @classmethod
    @override
    def get_segment_class(cls) -> type[MessageSegment]:
        return MessageSegment

    def to_rich_text(self, truncate: Optional[int] = 70) -> str:
        return "".join(seg.to_rich_text(truncate=truncate) for seg in self)

    @staticmethod
    @override
    def _construct(msg: str) -> Iterable[MessageSegment]:
        yield MessageSegment.text(msg)

    @override
    def extract_plain_text(self) -> str:
        return "".join(seg.data["text"] for seg in self if seg.is_text())

    def reduce(self) -> None:
        index = 1
        while index < len(self):
            if self[index - 1].type == "text" and self[index].type == "text":
                self[index - 1].data["text"] += self[index].data["text"]
                del self[index]
            else:
                index += 1
