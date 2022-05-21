from datetime import datetime
from typing_extensions import Literal
from typing import TYPE_CHECKING, Optional

from nonebot.typing import overrides
from nonebot.utils import escape_tag
from pydantic import Extra, BaseModel

from nonebot.adapters import Event as BaseEvent
from nonebot.adapters.onebot.exception import NoLogException

from .message import Message

if TYPE_CHECKING:
    from .bot import Bot


class Event(BaseEvent, extra=Extra.allow):
    """OneBot V12 协议事件，字段与 OneBot 一致

    参考文档：[OneBot 文档](https://12.1bot.dev)
    """

    id: str
    impl: str
    platform: str
    self_id: str
    time: datetime
    type: Literal["message", "notice", "request", "meta"]
    detail_type: str
    sub_type: str

    @overrides(BaseEvent)
    def get_type(self) -> str:
        return self.type

    @overrides(BaseEvent)
    def get_event_name(self) -> str:
        return ".".join(filter(None, (self.type, self.detail_type, self.sub_type)))

    @overrides(BaseEvent)
    def get_event_description(self) -> str:
        return escape_tag(str(self.dict()))

    @overrides(BaseEvent)
    def get_message(self) -> Message:
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


class Status(BaseModel, extra=Extra.allow):
    good: bool
    online: bool


class Reply(BaseModel, extra=Extra.allow):
    message_id: str
    user_id: str


# Message Event
class MessageEvent(Event):
    type: Literal["message"]
    message_id: str
    message: Message
    alt_message: str
    user_id: str

    to_me = False
    """
    :说明: 消息是否与机器人有关

    :类型: ``bool``
    """
    reply: Optional[Reply] = None
    """
    :说明: 消息中提取的回复消息，内容为 ``get_msg`` API 返回结果

    :类型: ``Optional[Reply]``
    """

    @overrides(Event)
    def get_message(self) -> Message:
        return self.message

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


class ChannelMessageEvent(MessageEvent):
    detail_type: Literal["channel"]
    guild_id: str
    channel_id: str

    @overrides(Event)
    def get_event_description(self) -> str:
        return (
            f"Message {self.message_id} from {self.user_id}@"
            f'[群组:{self.guild_id}, 频道:{self.channel_id}] "'
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
        return f"guild_{self.guild_id}_channel_{self.channel_id}_{self.user_id}"


class NoticeEvent(Event):
    type: Literal["notice"]


class FriendIncreaseEvent(NoticeEvent):
    detail_type: Literal["friend_increase"]
    user_id: str


class FriendDecreaseEvent(NoticeEvent):
    detail_type: Literal["friend_decrease"]
    user_id: str


class PrivateMessageDeleteEvent(NoticeEvent):
    detail_type: Literal["private_message_delete"]
    message_id: str


class GroupMemberIncreaseEvent(NoticeEvent):
    detail_type: Literal["group_member_increase"]
    group_id: str
    user_id: str
    operator_id: str


class GroupMemberDecreaseEvent(NoticeEvent):
    detail_type: Literal["group_member_decrease"]
    group_id: str
    user_id: str
    operator_id: str


class GroupMemberBanEvent(NoticeEvent):
    detail_type: Literal["group_member_ban"]
    group_id: str
    user_id: str
    operator_id: str


class GroupMemberUnbanEvent(NoticeEvent):
    detail_type: Literal["group_member_unban"]
    group_id: str
    user_id: str
    operator_id: str


class GroupAdminSetEvent(NoticeEvent):
    detail_type: Literal["group_admin_set"]
    group_id: str
    user_id: str
    operator_id: str


class GroupAdminUnsetEvent(NoticeEvent):
    detail_type: Literal["group_admin_unset"]
    group_id: str
    user_id: str
    operator_id: str


class GroupMessageDeleteEvent(NoticeEvent):
    detail_type: Literal["group_message_delete"]
    group_id: str
    message_id: str
    user_id: str
    operator_id: str


class GuildMemberIncreaseEvent(NoticeEvent):
    detail_type: Literal["guild_member_increase"]
    guild_id: str
    user_id: str
    operator_id: str


class GuildMemberDecreaseEvent(NoticeEvent):
    detail_type: Literal["guild_member_decrease"]
    guild_id: str
    user_id: str
    operator_id: str


class GuildMessageDeleteEvent(NoticeEvent):
    detail_type: Literal["guild_message_delete"]
    guild_id: str
    channel_id: str
    message_id: str
    user_id: str
    operator_id: str


class ChannelCreateEvent(NoticeEvent):
    detail_type: Literal["channel_create"]
    guild_id: str
    channel_id: str
    operator_id: str


class ChannelDeleteEvent(NoticeEvent):
    detail_type: Literal["channel_delete"]
    guild_id: str
    channel_id: str
    operator_id: str


# Request Events
class RequestEvent(Event):
    type: Literal["request"]


# Meta Events
class MetaEvent(Event):
    type: Literal["meta"]

    @overrides(Event)
    def get_log_string(self) -> str:
        raise NoLogException


class HeartbeatMetaEvent(MetaEvent):
    detail_type: Literal["heartbeat"]
    interval: int
    status: Status
