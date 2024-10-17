"""OneBot v11 事件模型。

FrontMatter:
    sidebar_position: 4
    description: onebot.v11.event 模块
"""

from copy import deepcopy
from typing_extensions import override
from typing import TYPE_CHECKING, Any, Literal, Optional

from pydantic import BaseModel
from nonebot.utils import escape_tag
from nonebot.compat import PYDANTIC_V2, ConfigDict, model_dump

from nonebot.adapters import Event as BaseEvent
from nonebot.adapters.onebot.compat import model_validator
from nonebot.adapters.onebot.utils import highlight_rich_message

from .message import Message
from .exception import NoLogException

if TYPE_CHECKING:
    from .bot import Bot


class Event(BaseEvent):
    """OneBot v11 协议事件，字段与 OneBot 一致。各事件字段参考 [OneBot 文档]

    [OneBot 文档]: https://github.com/botuniverse/onebot-11/blob/master/README.md
    """

    time: int
    self_id: int
    post_type: str

    @override
    def get_type(self) -> str:
        return self.post_type

    @override
    def get_event_name(self) -> str:
        return self.post_type

    @override
    def get_event_description(self) -> str:
        return escape_tag(str(model_dump(self)))

    @override
    def get_message(self) -> Message:
        raise ValueError("Event has no message!")

    @override
    def get_user_id(self) -> str:
        raise ValueError("Event has no context!")

    @override
    def get_session_id(self) -> str:
        raise ValueError("Event has no context!")

    @override
    def is_tome(self) -> bool:
        return False


# Models
class Sender(BaseModel):
    user_id: Optional[int] = None
    nickname: Optional[str] = None
    sex: Optional[str] = None
    age: Optional[int] = None
    card: Optional[str] = None
    area: Optional[str] = None
    level: Optional[str] = None
    role: Optional[str] = None
    title: Optional[str] = None

    if PYDANTIC_V2:
        model_config = ConfigDict(extra="allow")
    else:

        class Config(ConfigDict):
            extra = "allow"


class Reply(BaseModel):
    time: int
    message_type: str
    message_id: int
    real_id: int
    sender: Sender
    message: Message

    if PYDANTIC_V2:
        model_config = ConfigDict(extra="allow")
    else:

        class Config(ConfigDict):
            extra = "allow"


class Anonymous(BaseModel):
    id: int
    name: str
    flag: str

    if PYDANTIC_V2:
        model_config = ConfigDict(extra="allow")
    else:

        class Config(ConfigDict):
            extra = "allow"


class File(BaseModel):
    id: str
    name: str
    size: int
    busid: int

    if PYDANTIC_V2:
        model_config = ConfigDict(extra="allow")
    else:

        class Config(ConfigDict):
            extra = "allow"


class Status(BaseModel):
    online: bool
    good: bool

    if PYDANTIC_V2:
        model_config = ConfigDict(extra="allow")
    else:

        class Config(ConfigDict):
            extra = "allow"


# Message Events
class MessageEvent(Event):
    """消息事件"""

    post_type: Literal["message"]
    sub_type: str
    user_id: int
    message_type: str
    message_id: int
    message: Message
    original_message: Message
    raw_message: str
    font: int
    sender: Sender
    to_me: bool = False
    """
    :说明: 消息是否与机器人有关

    :类型: ``bool``
    """
    reply: Optional[Reply] = None
    """
    :说明: 消息中提取的回复消息，内容为 ``get_msg`` API 返回结果

    :类型: ``Optional[Reply]``
    """

    @model_validator(mode="before")
    def check_message(cls, values: dict[str, Any]) -> dict[str, Any]:
        if "message" in values:
            values["original_message"] = deepcopy(values["message"])
        return values

    @override
    def get_event_name(self) -> str:
        sub_type = getattr(self, "sub_type", None)
        return f"{self.post_type}.{self.message_type}" + (
            f".{sub_type}" if sub_type else ""
        )

    @override
    def get_message(self) -> Message:
        return self.message

    @override
    def get_user_id(self) -> str:
        return str(self.user_id)

    @override
    def get_session_id(self) -> str:
        return str(self.user_id)

    @override
    def is_tome(self) -> bool:
        return self.to_me


class PrivateMessageEvent(MessageEvent):
    """私聊消息"""

    message_type: Literal["private"]

    @override
    def get_event_description(self) -> str:
        return (
            f"Message {self.message_id} from {self.user_id} "
            f"{''.join(highlight_rich_message(repr(self.original_message.to_rich_text())))}"
        )


class GroupMessageEvent(MessageEvent):
    """群消息"""

    message_type: Literal["group"]
    group_id: int
    anonymous: Optional[Anonymous] = None

    @override
    def get_event_description(self) -> str:
        return (
            f"Message {self.message_id} from {self.user_id}@[群:{self.group_id}] "
            f"{''.join(highlight_rich_message(repr(self.original_message.to_rich_text())))}"
        )

    @override
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"


# Notice Events
class NoticeEvent(Event):
    """通知事件"""

    post_type: Literal["notice"]
    notice_type: str

    @override
    def get_event_name(self) -> str:
        sub_type = getattr(self, "sub_type", None)
        return f"{self.post_type}.{self.notice_type}" + (
            f".{sub_type}" if sub_type else ""
        )


class GroupUploadNoticeEvent(NoticeEvent):
    """群文件上传事件"""

    notice_type: Literal["group_upload"]
    user_id: int
    group_id: int
    file: File

    @override
    def get_user_id(self) -> str:
        return str(self.user_id)

    @override
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"


class GroupAdminNoticeEvent(NoticeEvent):
    """群管理员变动"""

    notice_type: Literal["group_admin"]
    sub_type: str
    user_id: int
    group_id: int

    @override
    def is_tome(self) -> bool:
        return self.user_id == self.self_id

    @override
    def get_user_id(self) -> str:
        return str(self.user_id)

    @override
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"


class GroupDecreaseNoticeEvent(NoticeEvent):
    """群成员减少事件"""

    notice_type: Literal["group_decrease"]
    sub_type: str
    user_id: int
    group_id: int
    operator_id: int

    @override
    def is_tome(self) -> bool:
        return self.user_id == self.self_id

    @override
    def get_user_id(self) -> str:
        return str(self.user_id)

    @override
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"


class GroupIncreaseNoticeEvent(NoticeEvent):
    """群成员增加事件"""

    notice_type: Literal["group_increase"]
    sub_type: str
    user_id: int
    group_id: int
    operator_id: int

    @override
    def is_tome(self) -> bool:
        return self.user_id == self.self_id

    @override
    def get_user_id(self) -> str:
        return str(self.user_id)

    @override
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"


class GroupBanNoticeEvent(NoticeEvent):
    """群禁言事件"""

    notice_type: Literal["group_ban"]
    sub_type: str
    user_id: int
    group_id: int
    operator_id: int
    duration: int

    @override
    def is_tome(self) -> bool:
        return self.user_id == self.self_id

    @override
    def get_user_id(self) -> str:
        return str(self.user_id)

    @override
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"


class FriendAddNoticeEvent(NoticeEvent):
    """好友添加事件"""

    notice_type: Literal["friend_add"]
    user_id: int

    @override
    def get_user_id(self) -> str:
        return str(self.user_id)

    @override
    def get_session_id(self) -> str:
        return str(self.user_id)


class GroupRecallNoticeEvent(NoticeEvent):
    """群消息撤回事件"""

    notice_type: Literal["group_recall"]
    user_id: int
    group_id: int
    operator_id: int
    message_id: int

    @override
    def is_tome(self) -> bool:
        return self.user_id == self.self_id

    @override
    def get_user_id(self) -> str:
        return str(self.user_id)

    @override
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"


class FriendRecallNoticeEvent(NoticeEvent):
    """好友消息撤回事件"""

    notice_type: Literal["friend_recall"]
    user_id: int
    message_id: int

    @override
    def get_user_id(self) -> str:
        return str(self.user_id)

    @override
    def get_session_id(self) -> str:
        return str(self.user_id)


class NotifyEvent(NoticeEvent):
    """提醒事件"""

    notice_type: Literal["notify"]
    sub_type: str
    user_id: int
    group_id: int

    @override
    def get_user_id(self) -> str:
        return str(self.user_id)

    @override
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"


class PokeNotifyEvent(NotifyEvent):
    """戳一戳提醒事件"""

    sub_type: Literal["poke"]
    target_id: int
    group_id: Optional[int] = None

    @override
    def is_tome(self) -> bool:
        return self.target_id == self.self_id

    @override
    def get_session_id(self) -> str:
        if not self.group_id:
            return str(self.user_id)
        return super().get_session_id()


class LuckyKingNotifyEvent(NotifyEvent):
    """群红包运气王提醒事件"""

    sub_type: Literal["lucky_king"]
    target_id: int

    @override
    def is_tome(self) -> bool:
        return self.target_id == self.self_id

    @override
    def get_user_id(self) -> str:
        return str(self.target_id)

    @override
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.target_id}"


class HonorNotifyEvent(NotifyEvent):
    """群荣誉变更提醒事件"""

    sub_type: Literal["honor"]
    honor_type: str

    @override
    def is_tome(self) -> bool:
        return self.user_id == self.self_id


# Request Events
class RequestEvent(Event):
    """请求事件"""

    post_type: Literal["request"]
    request_type: str

    @override
    def get_event_name(self) -> str:
        sub_type = getattr(self, "sub_type", None)
        return f"{self.post_type}.{self.request_type}" + (
            f".{sub_type}" if sub_type else ""
        )


class FriendRequestEvent(RequestEvent):
    """加好友请求事件"""

    request_type: Literal["friend"]
    user_id: int
    flag: str
    comment: Optional[str] = None

    @override
    def get_user_id(self) -> str:
        return str(self.user_id)

    @override
    def get_session_id(self) -> str:
        return str(self.user_id)

    async def approve(self, bot: "Bot", remark: str = ""):
        return await bot.set_friend_add_request(
            flag=self.flag, approve=True, remark=remark
        )

    async def reject(self, bot: "Bot"):
        return await bot.set_friend_add_request(flag=self.flag, approve=False)


class GroupRequestEvent(RequestEvent):
    """加群请求/邀请事件"""

    request_type: Literal["group"]
    sub_type: str
    group_id: int
    user_id: int
    flag: str
    comment: Optional[str] = None

    @override
    def get_user_id(self) -> str:
        return str(self.user_id)

    @override
    def get_session_id(self) -> str:
        return f"group_{self.group_id}_{self.user_id}"

    async def approve(self, bot: "Bot"):
        return await bot.set_group_add_request(
            flag=self.flag, sub_type=self.sub_type, approve=True
        )

    async def reject(self, bot: "Bot", reason: str = ""):
        return await bot.set_group_add_request(
            flag=self.flag, sub_type=self.sub_type, approve=False, reason=reason
        )


# Meta Events
class MetaEvent(Event):
    """元事件"""

    post_type: Literal["meta_event"]
    meta_event_type: str

    @override
    def get_event_name(self) -> str:
        sub_type = getattr(self, "sub_type", None)
        return f"{self.post_type}.{self.meta_event_type}" + (
            f".{sub_type}" if sub_type else ""
        )

    @override
    def get_log_string(self) -> str:
        raise NoLogException


class LifecycleMetaEvent(MetaEvent):
    """生命周期元事件"""

    meta_event_type: Literal["lifecycle"]
    sub_type: str


class HeartbeatMetaEvent(MetaEvent):
    """心跳元事件"""

    meta_event_type: Literal["heartbeat"]
    status: Status
    interval: int


__all__ = [
    "Event",
    "MessageEvent",
    "PrivateMessageEvent",
    "GroupMessageEvent",
    "NoticeEvent",
    "GroupUploadNoticeEvent",
    "GroupAdminNoticeEvent",
    "GroupDecreaseNoticeEvent",
    "GroupIncreaseNoticeEvent",
    "GroupBanNoticeEvent",
    "FriendAddNoticeEvent",
    "GroupRecallNoticeEvent",
    "FriendRecallNoticeEvent",
    "NotifyEvent",
    "PokeNotifyEvent",
    "LuckyKingNotifyEvent",
    "HonorNotifyEvent",
    "RequestEvent",
    "FriendRequestEvent",
    "GroupRequestEvent",
    "MetaEvent",
    "LifecycleMetaEvent",
    "HeartbeatMetaEvent",
]
