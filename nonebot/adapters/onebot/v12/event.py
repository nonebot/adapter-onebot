from typing_extensions import Literal

from pydantic import BaseModel

from nonebot.typing import overrides
from nonebot.utils import escape_tag
from nonebot.adapters import Event as BaseEvent

from .message import Message
from .exception import NoLogException


class Event(BaseEvent):
    """OneBot V12 协议事件，字段与 OneBot 一致

    参考文档：[OneBot 文档](https://12.1bot.dev)
    """

    __event__ = ""
    id: str
    impl: str
    platform: str
    self_id: str
    time: float
    type: str
    detail_type: str
    sub_type: str

    @overrides(BaseEvent)
    def get_type(self) -> str:
        return self.type

    @overrides(BaseEvent)
    def get_event_name(self) -> str:
        return self.__event__

    @overrides(BaseEvent)
    def get_event_description(self) -> str:
        return escape_tag(str(self.dict()))

    @overrides(BaseEvent)
    def get_message(self) -> Message:
        raise ValueError("Event has no message!")

    @overrides(BaseEvent)
    def get_plaintext(self) -> str:
        raise ValueError("Event has no message!")

    @overrides(BaseEvent)
    def get_user_id(self) -> str:
        raise ValueError("Event has no user_id!")

    @overrides(BaseEvent)
    def get_session_id(self) -> str:
        raise ValueError("Event has no session_id!")

    @overrides(BaseEvent)
    def is_tome(self) -> bool:
        return False


class Status(BaseModel):
    good: bool
    online: bool


class MessageEvent(Event):
    __event__ = "message"
    type: Literal["message"]
    message_id: str
    message: Message
    alt_message: str
    user_id: str

    to_me = False

    @overrides(Event)
    def get_message(self) -> Message:
        return self.message

    @overrides(Event)
    def get_plaintext(self) -> str:
        return self.message.extract_plain_text()

    @overrides(Event)
    def get_user_id(self) -> str:
        return self.user_id

    @overrides(Event)
    def get_session_id(self) -> str:
        return self.user_id

    @overrides(Event)
    def is_tome(self) -> bool:
        return self.to_me


class PrivateMessageEvent(MessageEvent):
    __event__ = "message.private"
    detail_type: Literal["private"]

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Message {self.message_id} from {self.user_id} "'
            + "".join(
                map(
                    lambda x: escape_tag(str(x))
                    if x.is_text()
                    else f"<le>{escape_tag(str(x))}</le>",
                    self.message,
                )
            )
            + '"'
        )


class GroupMessageEvent(MessageEvent):
    __event__ = "message.group"
    detail_type: Literal["group"]
    group_id: str

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f'Message {self.message_id} from {self.user_id}@[群:{self.group_id}] "'
            + "".join(
                map(
                    lambda x: escape_tag(str(x))
                    if x.is_text()
                    else f"<le>{escape_tag(str(x))}</le>",
                    self.message,
                )
            )
            + '"'
        )

    @overrides(MessageEvent)
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"


class NoticeEvent(Event):
    __event__ = "notice"
    type = Literal["notice"]


class RequestEvent(Event):
    __event__ = "request"
    type = Literal["request"]


class MetaEvent(Event):
    __event__ = "meta"
    type = Literal["meta"]

    @overrides(Event)
    def get_log_string(self) -> str:
        raise NoLogException


class HeartbeatMetaEvent(MetaEvent):
    __event__ = "meta.heartbeat"
    detail_type = Literal["heartbeat"]
    interval: int
    status: Status
