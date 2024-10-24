"""OneBot v11 消息类型。

FrontMatter:
    sidebar_position: 5
    description: onebot.v11.message 模块
"""

import re
from io import BytesIO
from pathlib import Path
from functools import partial
from typing import Union, Optional
from collections.abc import Iterable
from typing_extensions import Self, override

from nonebot.adapters.onebot.utils import b2s, f2s
from nonebot.adapters import Message as BaseMessage
from nonebot.adapters.onebot.utils import rich_escape
from nonebot.adapters.onebot.utils import truncate as trunc
from nonebot.adapters import MessageSegment as BaseMessageSegment

from .utils import escape, unescape


class MessageSegment(BaseMessageSegment["Message"]):
    """OneBot v11 协议 MessageSegment 适配。具体方法参考协议消息段类型或源码。"""

    @classmethod
    @override
    def get_message_class(cls) -> type["Message"]:
        return Message

    @override
    def __str__(self) -> str:
        if self.is_text():
            return escape(self.data.get("text", ""), escape_comma=False)

        params = ",".join(
            f"{k}={escape(str(v))}" for k, v in self.data.items() if v is not None
        )
        return f"[CQ:{self.type}{',' if params else ''}{params}]"

    def to_rich_text(self, truncate: Optional[int] = 70) -> str:
        if self.is_text():
            return rich_escape(self.data.get("text", ""), escape_comma=False)

        truncate_func = partial(trunc, length=truncate) if truncate else lambda x: x

        params = ",".join(
            f"{k}={rich_escape(truncate_func(str(v)))}"
            for k, v in self.data.items()
            if v is not None
        )
        return f"[{self.type}{':' if params else ''}{params}]"

    @override
    def __add__(
        self, other: Union[str, "MessageSegment", Iterable["MessageSegment"]]
    ) -> "Message":
        return Message(self) + (
            MessageSegment.text(other) if isinstance(other, str) else other
        )

    @override
    def __radd__(
        self, other: Union[str, "MessageSegment", Iterable["MessageSegment"]]
    ) -> "Message":
        return (
            MessageSegment.text(other) if isinstance(other, str) else Message(other)
        ) + self

    @override
    def is_text(self) -> bool:
        return self.type == "text"

    @classmethod
    def anonymous(cls, ignore_failure: Optional[bool] = None) -> Self:
        return cls("anonymous", {"ignore": b2s(ignore_failure)})

    @classmethod
    def at(cls, user_id: Union[int, str]) -> Self:
        return cls("at", {"qq": str(user_id)})

    @classmethod
    def contact(cls, type_: str, id: int) -> Self:
        return cls("contact", {"type": type_, "id": str(id)})

    @classmethod
    def contact_group(cls, group_id: int) -> Self:
        return cls("contact", {"type": "group", "id": str(group_id)})

    @classmethod
    def contact_user(cls, user_id: int) -> Self:
        return cls("contact", {"type": "qq", "id": str(user_id)})

    @classmethod
    def dice(cls) -> Self:
        return cls("dice", {})

    @classmethod
    def face(cls, id_: int) -> Self:
        return cls("face", {"id": str(id_)})

    @classmethod
    def forward(cls, id_: str) -> Self:
        return cls("forward", {"id": id_})

    @classmethod
    def image(
        cls,
        file: Union[str, bytes, BytesIO, Path],
        type_: Optional[str] = None,
        cache: bool = True,
        proxy: bool = True,
        timeout: Optional[int] = None,
    ) -> Self:
        return cls(
            "image",
            {
                "file": f2s(file),
                "type": type_,
                "cache": b2s(cache),
                "proxy": b2s(proxy),
                "timeout": timeout if timeout is None else str(timeout),
            },
        )

    @classmethod
    def json(cls, data: str) -> Self:
        return cls("json", {"data": data})

    @classmethod
    def location(
        cls,
        latitude: float,
        longitude: float,
        title: Optional[str] = None,
        content: Optional[str] = None,
    ) -> Self:
        return cls(
            "location",
            {
                "lat": str(latitude),
                "lon": str(longitude),
                "title": title,
                "content": content,
            },
        )

    @classmethod
    def music(cls, type_: str, id_: int) -> Self:
        return cls("music", {"type": type_, "id": str(id_)})

    @classmethod
    def music_custom(
        cls,
        url: str,
        audio: str,
        title: str,
        content: Optional[str] = None,
        img_url: Optional[str] = None,
    ) -> Self:
        return cls(
            "music",
            {
                "type": "custom",
                "url": url,
                "audio": audio,
                "title": title,
                "content": content,
                "image": img_url,
            },
        )

    @classmethod
    def node(cls, id_: int) -> Self:
        return cls("node", {"id": str(id_)})

    @classmethod
    def node_custom(
        cls, user_id: int, nickname: str, content: Union[str, "Message"]
    ) -> Self:
        return cls(
            "node", {"user_id": str(user_id), "nickname": nickname, "content": content}
        )

    @classmethod
    def poke(cls, type_: str, id_: str) -> Self:
        return cls("poke", {"type": type_, "id": id_})

    @classmethod
    def record(
        cls,
        file: Union[str, bytes, BytesIO, Path],
        magic: Optional[bool] = None,
        cache: Optional[bool] = None,
        proxy: Optional[bool] = None,
        timeout: Optional[int] = None,
    ) -> Self:
        return cls(
            "record",
            {
                "file": f2s(file),
                "magic": b2s(magic),
                "cache": b2s(cache),
                "proxy": b2s(proxy),
                "timeout": timeout if timeout is None else str(timeout),
            },
        )

    @classmethod
    def reply(cls, id_: int) -> Self:
        return cls("reply", {"id": str(id_)})

    @classmethod
    def rps(cls) -> Self:
        return cls("rps", {})

    @classmethod
    def shake(cls) -> Self:
        return cls("shake", {})

    @classmethod
    def share(
        cls,
        url: str = "",
        title: str = "",
        content: Optional[str] = None,
        image: Optional[str] = None,
    ) -> Self:
        return cls(
            "share", {"url": url, "title": title, "content": content, "image": image}
        )

    @classmethod
    def text(cls, text: str) -> Self:
        return cls("text", {"text": text})

    @classmethod
    def video(
        cls,
        file: Union[str, bytes, BytesIO, Path],
        cache: Optional[bool] = None,
        proxy: Optional[bool] = None,
        timeout: Optional[int] = None,
    ) -> Self:
        return cls(
            "video",
            {
                "file": f2s(file),
                "cache": b2s(cache),
                "proxy": b2s(proxy),
                "timeout": timeout,
            },
        )

    @classmethod
    def xml(cls, data: str) -> Self:
        return cls("xml", {"data": data})


class Message(BaseMessage[MessageSegment]):
    """OneBot v11 协议 Message 适配。"""

    @classmethod
    @override
    def get_segment_class(cls) -> type[MessageSegment]:
        return MessageSegment

    @override
    def __add__(
        self, other: Union[str, MessageSegment, Iterable[MessageSegment]]
    ) -> Self:
        return super().__add__(
            MessageSegment.text(other) if isinstance(other, str) else other
        )

    def to_rich_text(self, truncate: Optional[int] = 70) -> str:
        return "".join(seg.to_rich_text(truncate=truncate) for seg in self)

    @override
    def __radd__(
        self, other: Union[str, MessageSegment, Iterable[MessageSegment]]
    ) -> Self:
        return super().__radd__(
            MessageSegment.text(other) if isinstance(other, str) else other
        )

    @override
    def __iadd__(
        self, other: Union[str, MessageSegment, Iterable[MessageSegment]]
    ) -> Self:
        return super().__iadd__(
            MessageSegment.text(other) if isinstance(other, str) else other
        )

    @staticmethod
    @override
    def _construct(msg: str) -> Iterable[MessageSegment]:
        def _iter_message(msg: str) -> Iterable[tuple[str, str]]:
            text_begin = 0
            for cqcode in re.finditer(
                r"\[CQ:(?P<type>[a-zA-Z0-9-_.]+)"
                r"(?P<params>"
                r"(?:,[a-zA-Z0-9-_.]+=[^,\]]*)*"
                r"),?\]",
                msg,
            ):
                yield "text", msg[text_begin : cqcode.pos + cqcode.start()]
                text_begin = cqcode.pos + cqcode.end()
                yield cqcode.group("type"), cqcode.group("params").lstrip(",")
            yield "text", msg[text_begin:]

        for type_, data in _iter_message(msg):
            if type_ == "text":
                if data:
                    # only yield non-empty text segment
                    yield MessageSegment(type_, {"text": unescape(data)})
            else:
                data = {
                    k: unescape(v)
                    for k, v in (
                        x.split("=", maxsplit=1)
                        for x in filter(
                            lambda x: x, (x.lstrip() for x in data.split(","))
                        )
                    )
                }
                yield MessageSegment(type_, data)

    @override
    def extract_plain_text(self) -> str:
        return "".join(seg.data["text"] for seg in self if seg.is_text())

    def reduce(self) -> None:
        """合并消息内连续的纯文本段。"""
        index = 1
        while index < len(self):
            if self[index - 1].type == "text" and self[index].type == "text":
                self[index - 1].data["text"] += self[index].data["text"]
                del self[index]
            else:
                index += 1
