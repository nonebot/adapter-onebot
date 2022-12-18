"""OneBot v12 事件模型。

FrontMatter:
    sidebar_position: 4
    description: onebot.v12.event 模块
"""

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from nonebot.typing import overrides
from nonebot.utils import escape_tag
from pydantic import Extra, BaseModel, root_validator

from nonebot.adapters import Event as BaseEvent

from .message import Message
from .exception import NoLogException


class Event(BaseEvent, extra=Extra.allow):
    """OneBot V12 协议事件，字段与 OneBot 一致

    参考文档：[OneBot 文档](https://12.1bot.dev)
    """

    id: str
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


class BotSelf(BaseModel, extra=Extra.allow):
    """机器人自身标识"""

    platform: str
    user_id: str


class BotStatus(BaseModel, extra=Extra.allow):
    """机器人的状态"""

    self: BotSelf
    online: bool


class Status(BaseModel, extra=Extra.allow):
    """运行状态"""

    good: bool
    bots: List[BotStatus]


class Reply(BaseModel, extra=Extra.allow):
    message_id: str
    user_id: str


class BotEvent(Event):
    """包含 self 字段的机器人事件"""

    self: BotSelf


# Message Event
class MessageEvent(BotEvent):
    """消息事件"""

    type: Literal["message"]
    message_id: str
    message: Message
    original_message: Message
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

    @root_validator(pre=True, allow_reuse=True)
    def check_message(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if "message" in values:
            values["original_message"] = deepcopy(values["message"])
        return values

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
    """私聊消息"""

    detail_type: Literal["private"]

    @overrides(Event)
    def get_event_description(self) -> str:
        texts: List[str] = []
        msg_string: List[str] = []
        for seg in self.original_message:
            if seg.is_text():
                texts.append(str(seg))
            else:
                msg_string.extend(
                    (escape_tag("".join(texts)), f"<le>{escape_tag(str(seg))}</le>")
                )
                texts.clear()
        msg_string.append(escape_tag("".join(texts)))
        return (
            f'Message {self.message_id} from {self.user_id} "'
            + "".join(msg_string)
            + '"'
        )


class GroupMessageEvent(MessageEvent):
    """群消息"""

    detail_type: Literal["group"]
    group_id: str

    @overrides(Event)
    def get_event_description(self) -> str:
        texts: List[str] = []
        msg_string: List[str] = []
        for seg in self.original_message:
            if seg.is_text():
                texts.append(str(seg))
            else:
                msg_string.extend(
                    (escape_tag("".join(texts)), f"<le>{escape_tag(str(seg))}</le>")
                )
                texts.clear()
        msg_string.append(escape_tag("".join(texts)))
        return (
            f'Message {self.message_id} from {self.user_id}@[群:{self.group_id}] "'
            + "".join(msg_string)
            + '"'
        )

    @overrides(MessageEvent)
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"


class ChannelMessageEvent(MessageEvent):
    """频道消息"""

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


class NoticeEvent(BotEvent):
    """通知事件"""

    type: Literal["notice"]


class FriendIncreaseEvent(NoticeEvent):
    """好友增加事件"""

    detail_type: Literal["friend_increase"]
    user_id: str


class FriendDecreaseEvent(NoticeEvent):
    """好友减少事件"""

    detail_type: Literal["friend_decrease"]
    user_id: str


class PrivateMessageDeleteEvent(NoticeEvent):
    """私聊消息删除"""

    detail_type: Literal["private_message_delete"]
    message_id: str


class GroupMemberIncreaseEvent(NoticeEvent):
    """群成员增加事件"""

    detail_type: Literal["group_member_increase"]
    group_id: str
    user_id: str
    operator_id: str


class GroupMemberDecreaseEvent(NoticeEvent):
    """群成员减少事件"""

    detail_type: Literal["group_member_decrease"]
    group_id: str
    user_id: str
    operator_id: str


class GroupMemberBanEvent(NoticeEvent):
    """群成员禁言事件"""

    detail_type: Literal["group_member_ban"]
    group_id: str
    user_id: str
    operator_id: str


class GroupMemberUnbanEvent(NoticeEvent):
    """群成员解除禁言事件"""

    detail_type: Literal["group_member_unban"]
    group_id: str
    user_id: str
    operator_id: str


class GroupAdminSetEvent(NoticeEvent):
    """群管理员设置事件"""

    detail_type: Literal["group_admin_set"]
    group_id: str
    user_id: str
    operator_id: str


class GroupAdminUnsetEvent(NoticeEvent):
    """群管理员取消设置事件"""

    detail_type: Literal["group_admin_unset"]
    group_id: str
    user_id: str
    operator_id: str


class GroupMessageDeleteEvent(NoticeEvent):
    """群消息删除事件"""

    detail_type: Literal["group_message_delete"]
    group_id: str
    message_id: str
    user_id: str
    operator_id: str


class GuildMemberIncreaseEvent(NoticeEvent):
    """群组成员增加事件"""

    detail_type: Literal["guild_member_increase"]
    guild_id: str
    user_id: str
    operator_id: str


class GuildMemberDecreaseEvent(NoticeEvent):
    """群组成员减少事件"""

    detail_type: Literal["guild_member_decrease"]
    guild_id: str
    user_id: str
    operator_id: str


class ChannelMessageDeleteEvent(NoticeEvent):
    """频道消息删除事件"""

    detail_type: Literal["channel_message_delete"]
    guild_id: str
    channel_id: str
    message_id: str
    user_id: str
    operator_id: str


class ChannelCreateEvent(NoticeEvent):
    """频道新建事件"""

    detail_type: Literal["channel_create"]
    guild_id: str
    channel_id: str
    operator_id: str


class ChannelDeleteEvent(NoticeEvent):
    """频道删除事件"""

    detail_type: Literal["channel_delete"]
    guild_id: str
    channel_id: str
    operator_id: str


# Request Events
class RequestEvent(BotEvent):
    """请求事件"""

    type: Literal["request"]


# Meta Events
class MetaEvent(Event):
    """元事件"""

    type: Literal["meta"]

    @overrides(Event)
    def get_log_string(self) -> str:
        raise NoLogException


class ImplVersion(BaseModel, extra=Extra.allow):
    impl: str
    version: str
    onebot_version: str


class ConnectMetaEvent(MetaEvent):
    """连接事件"""

    detail_type: Literal["connect"]
    version: ImplVersion


class HeartbeatMetaEvent(MetaEvent):
    """心跳事件"""

    detail_type: Literal["heartbeat"]
    interval: int
    status: Status


class StatusUpdateMetaEvent(MetaEvent):
    """状态更新事件"""

    detail_type: Literal["status_update"]
    status: Status
