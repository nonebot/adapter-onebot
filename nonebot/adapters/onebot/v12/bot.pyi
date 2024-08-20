from typing import Any, Literal, TypedDict, overload

from nonebot.adapters import Bot as BaseBot

from .adapter import Adapter
from .event import Event as EventModel
from .message import Message, MessageSegment
from .event import BotStatus as BotStatusModel
from .event import MessageEvent as MessageEventModel

class Event(TypedDict):
    id: str
    time: float
    type: Literal["message", "notice", "request", "meta"]
    detail_type: str
    sub_type: str

class BotSelf(TypedDict):
    platform: str
    user_id: str

class BotStatus(TypedDict):
    self: BotSelf
    online: bool

class GetStatusResp(TypedDict):
    good: str
    bots: list[BotStatus]

class GetVersionResp(TypedDict):
    impl: str
    version: str
    onebot_version: str

class SendMessageResp(TypedDict):
    message_id: str
    time: float

class GetSelfInfoResp(TypedDict):
    user_id: str
    user_name: str
    user_displayname: str

class GetUserInfoResp(TypedDict):
    user_id: str
    user_name: str
    user_displayname: str
    user_remark: str

class GetGroupInfoResp(TypedDict):
    group_id: str
    group_name: str

class GetGroupMemberInfoResp(TypedDict):
    user_id: str
    user_name: str
    user_displayname: str

class GetGuildInfoResp(TypedDict):
    guild_id: str
    guild_name: str

class GetGuildMemberInfoResp(TypedDict):
    user_id: str
    user_name: str
    user_displayname: str

class GetChannelInfoResp(TypedDict):
    channel_id: str
    channel_name: str

class GetChannelMemberInfoResp(TypedDict):
    user_id: str
    user_name: str
    user_displayname: str

class UploadFileResp(TypedDict):
    file_id: str

class UploadFileFragmentedResp(TypedDict):
    file_id: str

class GetFileUrlResp(TypedDict):
    name: str
    url: str
    headers: dict[str, str] | None
    sha256: str | None

class GetFilePathResp(TypedDict):
    name: str
    path: str
    sha256: str | None

class GetFileDataResp(TypedDict):
    name: str
    data: str | bytes
    sha256: str | None

class GetFileFragmentedPrepareResp(TypedDict):
    name: str
    total_size: int
    sha256: str

class GetFileFragmentedTransferResp(TypedDict):
    data: str | bytes

def _check_reply(bot: Bot, event: MessageEventModel): ...
def _check_to_me(bot: Bot, event: MessageEventModel): ...
def _check_nickname(bot: Bot, event: MessageEventModel): ...
async def send(
    bot: Bot,
    event: EventModel,
    message: str | Message | MessageSegment,
    at_sender: bool = ...,
    reply_message: bool = ...,
    **kwargs: Any,
) -> Any: ...

class Bot(BaseBot):
    impl: str
    platform: str
    status: BotStatusModel | None
    def __init__(
        self,
        adapter: Adapter,
        self_id: str,
        impl: str,
        platform: str,
        status: BotStatusModel | None = ...,
    ) -> None: ...
    async def call_api(self, api: str, **data) -> Any:
        """调用 OneBot 协议 API。

        参数:
            api: API 名称
            data: API 参数

        返回:
            API 调用返回数据

        异常:
            nonebot.adapters.onebot.exception.NetworkError: 网络错误
            nonebot.adapters.onebot.exception.ActionFailed: API 调用失败
        """

    async def handle_event(self, event: EventModel) -> None: ...
    async def send(
        self, event: EventModel, message: str | Message | MessageSegment, **kwargs: Any
    ) -> Any: ...
    async def get_latest_events(
        self, *, limit: int = ..., timeout: int = ..., **kwargs: Any
    ) -> list[Event]:
        """获取最新事件列表

        参数:
            limit: 获取的事件数量上限，0 表示不限制
            timeout: 没有事件时要等待的秒数，0 表示使用短轮询，不等待
            kwargs: 扩展字段
        """

    async def get_supported_actions(self, **kwargs: Any) -> list[str]:
        """获取支持的动作列表

        参数:
            kwargs: 扩展字段
        """

    async def get_status(self, **kwargs: Any) -> GetStatusResp:
        """获取运行状态

        参数:
            kwargs: 扩展字段
        """

    async def get_version(self, **kwargs: Any) -> GetVersionResp:
        """获取版本信息

        参数:
            kwargs: 扩展字段
        """

    async def send_message(
        self,
        *,
        detail_type: Literal["private", "group", "channel"] | str,  # noqa: PYI051
        user_id: str = ...,
        group_id: str = ...,
        guild_id: str = ...,
        channel_id: str = ...,
        message: Message,
        **kwargs: Any,
    ) -> SendMessageResp:
        """发送消息

        参数:
            detail_type: 发送的类型，
                可以为 private、group 或扩展的类型，和消息事件的 detail_type 字段对应
            user_id: 用户 ID，当 detail_type 为 private 时必须传入
            group_id: 群 ID，当 detail_type 为 group 时必须传入
            guild_id: Guild 群组 ID，当 detail_type 为 channel 时必须传入
            channel_id: 频道 ID，当 detail_type 为 channel 时必须传入
            message: 消息内容
            kwargs: 扩展字段
        """

    async def delete_message(self, *, message_id: str, **kwargs: Any) -> None:
        """撤回消息

        参数:
            message_id: 唯一的消息 ID
        """

    async def get_self_info(self, **kwargs: Any) -> GetSelfInfoResp:
        """获取机器人自身信息"""

    async def get_user_info(self, *, user_id: str, **kwargs: Any) -> GetUserInfoResp:
        """获取用户信息

        参数:
            user_id: 用户 ID，可以是好友，也可以是陌生人
            kwargs: 扩展字段
        """

    async def get_friend_list(self, **kwargs: Any) -> list[GetUserInfoResp]:
        """获取好友列表

        参数:
            kwargs: 扩展字段
        """

    async def get_group_info(self, *, group_id: str, **kwargs: Any) -> GetGroupInfoResp:
        """获取群信息

        参数:
            group_id: 群 ID
            kwargs: 扩展字段
        """

    async def get_group_list(self, **kwargs: Any) -> list[GetGroupInfoResp]:
        """获取群列表

        参数:
            kwargs: 扩展字段
        """

    async def get_group_member_info(
        self, *, group_id: str, user_id: str, **kwargs: Any
    ) -> GetGroupMemberInfoResp:
        """获取群成员信息

        参数:
            group_id: 群 ID
            user_id: 用户 ID
            kwargs: 扩展字段
        """

    async def get_group_member_list(
        self, *, group_id: str, **kwargs: Any
    ) -> list[GetGroupMemberInfoResp]:
        """获取群成员列表

        参数:
            group_id: 群 ID
            kwargs: 扩展字段
        """

    async def set_group_name(
        self, *, group_id: str, group_name: str, **kwargs: Any
    ) -> None:
        """设置群名称

        参数:
            group_id: 群 ID
            group_name: 群名称
            kwargs: 扩展字段
        """

    async def leave_group(self, *, group_id: str, **kwargs: Any) -> None:
        """退出群

        参数:
            group_id: 群 ID
            kwargs: 扩展字段
        """

    async def get_guild_info(self, *, guild_id: str, **kwargs: Any) -> GetGuildInfoResp:
        """获取 Guild 信息

        参数:
            guild_id: 群组 ID
            kwargs: 扩展字段
        """

    async def get_guild_list(self, **kwargs: Any) -> list[GetGuildInfoResp]:
        """获取群组列表

        参数:
            kwargs: 扩展字段
        """

    async def set_guild_name(
        self, *, guild_id: str, guild_name: str, **kwargs: Any
    ) -> None:
        """设置群组名称

        参数:
            guild_id: 群组 ID
            guild_name: 群组名称
            kwargs: 扩展字段
        """

    async def get_guild_member_info(
        self, *, guild_id: str, user_id: str, **kwargs: Any
    ) -> GetGuildMemberInfoResp:
        """获取群组成员信息

        参数:
            guild_id: 群组 ID
            user_id: 用户 ID
            kwargs: 扩展字段
        """

    async def get_guild_member_list(
        self, *, guild_id: str, **kwargs: Any
    ) -> list[GetGuildMemberInfoResp]:
        """获取群组成员列表

        参数:
            guild_id: 群组 ID
            kwargs: 扩展字段
        """

    async def leave_guild(self, *, guild_id: str, **kwargs: Any) -> None:
        """退出群组

        参数:
            guild_id: 群组 ID
            kwargs: 扩展字段
        """

    async def get_channel_info(
        self, *, guild_id: str, channel_id: str, **kwargs: Any
    ) -> GetChannelInfoResp:
        """获取频道信息

        参数:
            guild_id: 群组 ID
            channel_id: 频道 ID
            kwargs: 扩展字段
        """

    async def get_channel_list(
        self, *, guild_id: str, joined_only: bool = False, **kwargs: Any
    ) -> list[GetChannelInfoResp]:
        """获取频道列表

        参数:
            guild_id: 群组 ID
            joined_only: 只获取机器人账号已加入的频道列表
            kwargs: 扩展字段
        """

    async def set_channel_name(
        self, *, guild_id: str, channel_id: str, channel_name: str, **kwargs: Any
    ) -> None:
        """设置频道名称

        参数:
            guild_id: 群组 ID
            channel_id: 频道 ID
            channel_name: 新频道名称
            kwargs: 扩展字段
        """

    async def get_channel_member_info(
        self, *, guild_id: str, channel_id: str, user_id: str, **kwargs: Any
    ) -> GetChannelMemberInfoResp:
        """获取频道成员信息

        参数:
            guild_id: 群组 ID
            channel_id: 频道 ID
            user_id: 用户 ID
            kwargs: 扩展字段
        """

    async def get_channel_member_list(
        self, *, guild_id: str, channel_id: str, **kwargs: Any
    ) -> list[GetChannelMemberInfoResp]:
        """获取频道成员列表

        参数:
            guild_id: 群组 ID
            channel_id: 频道 ID
            kwargs: 扩展字段
        """

    async def leave_channel(
        self, *, guild_id: str, channel_id: str, **kwargs: Any
    ) -> None:
        """退出频道

        参数:
            guild_id: 群组 ID
            channel_id: 频道 ID
            kwargs: 扩展字段
        """

    async def upload_file(
        self,
        *,
        type: Literal["url", "path", "data"] | str,  # noqa: PYI051
        name: str,
        url: str = ...,
        headers: dict[str, str] = ...,
        path: str = ...,
        data: bytes = ...,
        sha256: str = ...,
        **kwargs: Any,
    ) -> UploadFileResp:
        """上传文件

        参数:
            type: 上传文件的方式，可以为 url、path、data 或扩展的方式
            name: 文件名
            url: 文件 URL，当 type 为 url 时必须传入
            headers: 下载 URL 时需要添加的 HTTP 请求头，可选传入
            path: 文件路径，当 type 为 path 时必须传入
            data: 文件数据，当 type 为 data 时必须传入
            sha256: 文件数据（原始二进制）的 SHA256 校验和，全小写，可选传入
            kwargs: 扩展字段
        """

    @overload
    async def upload_file_fragmented(
        self,
        stage: Literal["prepare"],
        name: str = ...,
        total_size: int = ...,
        **kwargs: Any,
    ) -> UploadFileFragmentedResp:
        """分片上传文件，准备阶段

        参数:
            stage: 上传阶段
            name: 文件名
            total_size: 文件完整大小
            kwargs: 扩展字段
        """

    @overload
    async def upload_file_fragmented(
        self,
        stage: Literal["transfer"],
        file_id: str = ...,
        offset: int = ...,
        data: bytes = ...,
        **kwargs: Any,
    ) -> None:
        """分片上传阶段，传输阶段

        参数:
            stage: 上传阶段
            file_id: 准备阶段返回的文件 ID
            offset: 本次传输的文件偏移，单位：字节
            data: 本次传输的文件数据
            kwargs: 扩展字段
        """

    @overload
    async def upload_file_fragmented(
        self,
        stage: Literal["finish"],
        file_id: str = ...,
        sha256: str = ...,
        **kwargs: Any,
    ) -> UploadFileResp:
        """分片上传文件，结束阶段

        参数:
            stage: 上传阶段
            file_id: 准备阶段返回的文件 ID
            sha256: 整个文件的 SHA256 校验和，全小写
            kwargs: 扩展字段
        """

    @overload
    async def get_file(
        self,
        *,
        type: Literal["url"],
        file_id: str,
        **kwargs: Any,
    ) -> GetFileUrlResp:
        """获取文件

        参数:
            type: 获取文件的方式，可以为 url、path、data 或扩展的方式
            file_id: 文件 ID
            kwargs: 扩展字段
        """

    @overload
    async def get_file(
        self,
        *,
        type: Literal["path"],
        file_id: str,
        **kwargs: Any,
    ) -> GetFilePathResp:
        """获取文件

        参数:
            type: 获取文件的方式，可以为 url、path、data 或扩展的方式
            file_id: 文件 ID
            kwargs: 扩展字段
        """

    @overload
    async def get_file(
        self,
        *,
        type: Literal["data"],
        file_id: str,
        **kwargs: Any,
    ) -> GetFileDataResp:
        """获取文件

        参数:
            type: 获取文件的方式，可以为 url、path、data 或扩展的方式
            file_id: 文件 ID
            kwargs: 扩展字段
        """

    @overload
    async def get_file_fragmented(
        self,
        *,
        stage: Literal["prepare"],
        file_id: str,
        **kwargs: Any,
    ) -> GetFileFragmentedPrepareResp:
        """分片获取文件，准备阶段

        参数:
            stage: 获取阶段
            file_id: 文件 ID
            kwargs: 扩展字段
        """

    @overload
    async def get_file_fragmented(
        self,
        *,
        stage: Literal["transfer"],
        file_id: str,
        offset: int = ...,
        size: int = ...,
    ) -> GetFileFragmentedTransferResp:
        """分片获取文件，传输阶段

        参数:
            stage: 获取阶段
            file_id: 文件 ID
            offset: 本次获取的文件偏移，单位：字节
            size: 本次获取的文件大小，单位：字节
            kwargs: 扩展字段
        """
