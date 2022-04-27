from typing import Dict, Iterable, Type, Union, Any

from nonebot.typing import overrides
from nonebot.adapters import Message as BaseMessage
from nonebot.adapters import MessageSegment as BaseMessageSegment


class MessageSegment(BaseMessageSegment["Message"]):
    @classmethod
    @overrides(BaseMessageSegment)
    def get_message_class(cls) -> BaseMessage["Message"]:
        return Message

    @overrides(BaseMessageSegment)
    def __str__(self) -> str:
        if self.type == "text":
            return self.data.get("text", "")
        params = ",".join(
            [f"{k}={str(v)}" for k, v in self.data.items() if v is not None]
        )
        return f"[{self.type}:{params}]"

    @overrides(BaseMessageSegment)
    def __add__(
        self, other: Union[str, "MessageSegment", Iterable["MessageSegment"]]
    ) -> "Message":
        return Message(self) + (
            MessageSegment.text(other) if isinstance(other, str) else other
        )

    @overrides(BaseMessageSegment)
    def __radd__(
        self, other: Union[str, "MessageSegment", Iterable["MessageSegment"]]
    ) -> "Message":
        return (
            MessageSegment.text(other) if isinstance(other, str) else Message(other)
        ) + self

    @overrides(BaseMessageSegment)
    def is_text(self) -> bool:
        return self.type == "text"

    @staticmethod
    def text(text: str, extra: Dict[str, Any] = {}) -> "MessageSegment":
        extra["text"] = text
        return MessageSegment("text", extra)

    @staticmethod
    def mention(user_id: str, extra: Dict[str, Any] = {}) -> "MessageSegment":
        extra["user_id"] = user_id
        return MessageSegment("mention", extra)

    @staticmethod
    def mention_all(extra: Dict[str, Any] = {}) -> "MessageSegment":
        return MessageSegment("mention_all", extra)

    @staticmethod
    def image(file_id: str, extra: Dict[str, Any] = {}) -> "MessageSegment":
        extra["file_id"] = file_id
        return MessageSegment("image", extra)

    @staticmethod
    def voice(file_id: str, extra: Dict[str, Any] = {}) -> "MessageSegment":
        extra["file_id"] = file_id
        return MessageSegment("voice", extra)

    @staticmethod
    def audio(file_id: str, extra: Dict[str, Any] = {}) -> "MessageSegment":
        extra["file_id"] = file_id
        return MessageSegment("audio", extra)

    @staticmethod
    def video(file_id: str, extra: Dict[str, Any] = {}) -> "MessageSegment":
        extra["file_id"] = file_id
        return MessageSegment("video", extra)

    @staticmethod
    def file(file_id: str, extra: Dict[str, Any] = {}) -> "MessageSegment":
        extra["file_id"] = file_id
        return MessageSegment("file", extra)

    @staticmethod
    def location(
        latitude: float,
        longitude: float,
        title: str,
        content: str,
        extra: Dict[str, Any] = {},
    ) -> "MessageSegment":
        extra["latitude"] = latitude
        extra["longitude"] = longitude
        extra["title"] = title
        extra["content"] = content
        return MessageSegment(
            "location",
            extra,
        )

    @staticmethod
    def reply(
        message_id: str, user_id: str, extra: Dict[str, Any] = {}
    ) -> "MessageSegment":
        extra["message_id"] = message_id
        extra["user_id"] = user_id
        return MessageSegment("reply", extra)


class Message(BaseMessage[MessageSegment]):
    @classmethod
    @overrides(BaseMessage)
    def get_segment_class(cls) -> Type[MessageSegment]:
        return MessageSegment

    @overrides(BaseMessage)
    def __add__(
        self, other: Union[str, MessageSegment, Iterable[MessageSegment]]
    ) -> "Message":
        return super(Message, self).__add__(
            MessageSegment.text(other) if isinstance(other, str) else other
        )

    @overrides(BaseMessage)
    def __radd__(
        self, other: Union[str, MessageSegment, Iterable[MessageSegment]]
    ) -> "Message":
        return super(Message, self).__radd__(
            MessageSegment.text(other) if isinstance(other, str) else other
        )

    @staticmethod
    @overrides(BaseMessage)
    def _construct(msg: str) -> Iterable[MessageSegment]:
        yield MessageSegment.text(msg)

    @overrides(BaseMessage)
    def extract_plain_text(self) -> str:
        return "".join(seg.data["text"] for seg in self if seg.is_text())

    def ruduce(self) -> None:
        index = 1
        while index < len(self):
            if self[index - 1].type == "text" and self[index].type == "text":
                self[index - 1].data["text"] += self[index].data["text"]
                del self[index]
            else:
                index += 1
