from ast import operator
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

    id: str
    impl: str
    platform: str
    self_id: str
    time: float
    type: Literal["message", "notice", "request", "meta"]
    detail_type: str
    sub_type: str

    @overrides(BaseEvent)
    def get_type(self) -> str:
        return self.type

    @overrides(BaseEvent)
    def get_event_name(self) -> str:
        return self.full_type()

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

    @classmethod
    def full_type(cls) -> str:
        return ".".join(
            [
                i
                for i in [
                    cls.__fields__["type"].default,
                    cls.__fields__["detail_type"].default,
                    cls.__fields__["sub_type"].default,
                ]
                if i
            ]
        )


class Status(BaseModel):
    good: bool
    online: bool


class MessageEvent(Event):
    type: Literal["message"] = "message"
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
    detail_type: Literal["private"] = "private"

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
    detail_type: Literal["group"] = "group"
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
    type: Literal["notice"] = "notice"


class FriendIncreaseEvent(NoticeEvent):
    detail_type: Literal["friend_increase"] = "friend_increase"
    uer_id: str


class FriendDecreaseEvent(NoticeEvent):
    detail_type: Literal["friend_decrease"] = "friend_decrease"
    user_id: str


class PrivateMessageDeleteEvent(NoticeEvent):
    detail_type: Literal["private_message_delete"] = "private_message_delete"
    message_id: str


class GroupMemberIncreaseEvent(NoticeEvent):
    detail_type: Literal["group_member_increase"] = "group_member_increase"
    group_id: str
    user_id: str
    operator_id: str


class GroupMemberDecreaseEvent(NoticeEvent):
    detail_type: Literal["group_member_decrease"] = "group_member_decrease"
    group_id: str
    user_id: str
    operator_id: str


class GroupMemberBanEvent(NoticeEvent):
    detail_type: Literal["group_member_ban"] = "group_member_ban"
    group_id: str
    user_id: str
    operator_id: str


class GroupMemberUnbanEvent(NoticeEvent):
    detail_type: Literal["group_member_unban"] = "group_member_unban"
    group_id: str
    user_id: str
    operator_id: str


class GroupAdminSetEvent(NoticeEvent):
    detail_type: Literal["group_admin_set"] = "group_admin_set"
    group_id: str
    user_id: str
    operator_id: str


class GroupAdminUnsetEvent(NoticeEvent):
    detail_type: Literal["group_admin_unset"] = "group_admin_unset"
    group_id: str
    user_id: str
    operator_id: str


class GroupMessageDeleteEvent(NoticeEvent):
    detail_type: Literal["group_message_delete"] = "group_message_delete"
    group_id: str
    message_id: str
    user_id: str
    operator_id: str


class RequestEvent(Event):
    type: Literal["request"] = "request"


class MetaEvent(Event):
    type: Literal["meta"] = "meta"

    @overrides(Event)
    def get_log_string(self) -> str:
        raise NoLogException


class HeartbeatMetaEvent(MetaEvent):
    detail_type: Literal["heartbeat"] = "heartbeat"
    interval: int
    status: Status
