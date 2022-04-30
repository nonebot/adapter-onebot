from typing import Iterable, Type, Union

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
    def text(text: str, **kwargs) -> "MessageSegment":
        kwargs["text"] = text
        return MessageSegment("text", kwargs)

    @staticmethod
    def mention(user_id: str, **kwargs) -> "MessageSegment":
        kwargs["user_id"] = user_id
        return MessageSegment("mention", kwargs)

    @staticmethod
    def mention_all(**kwargs) -> "MessageSegment":
        return MessageSegment("mention_all", kwargs)

    @staticmethod
    def image(file_id: str, **kwargs) -> "MessageSegment":
        kwargs["file_id"] = file_id
        return MessageSegment("image", kwargs)

    @staticmethod
    def voice(file_id: str, **kwargs) -> "MessageSegment":
        kwargs["file_id"] = file_id
        return MessageSegment("voice", kwargs)

    @staticmethod
    def audio(file_id: str, **kwargs) -> "MessageSegment":
        kwargs["file_id"] = file_id
        return MessageSegment("audio", kwargs)

    @staticmethod
    def video(file_id: str, **kwargs) -> "MessageSegment":
        kwargs["file_id"] = file_id
        return MessageSegment("video", kwargs)

    @staticmethod
    def file(file_id: str, **kwargs) -> "MessageSegment":
        kwargs["file_id"] = file_id
        return MessageSegment("file", kwargs)

    @staticmethod
    def location(
        latitude: float,
        longitude: float,
        title: str,
        content: str,
        **kwargs,
    ) -> "MessageSegment":
        kwargs["latitude"] = latitude
        kwargs["longitude"] = longitude
        kwargs["title"] = title
        kwargs["content"] = content
        return MessageSegment(
            "location",
            kwargs,
        )

    @staticmethod
    def reply(message_id: str, user_id: str, **kwargs) -> "MessageSegment":
        kwargs["message_id"] = message_id
        kwargs["user_id"] = user_id
        return MessageSegment("reply", kwargs)


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
