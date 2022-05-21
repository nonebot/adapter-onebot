from typing import Any, Dict, List, Union, Optional

from nonebot.adapters import Bot as BaseBot

from .event import Event, MessageEvent
from .message import Message, MessageSegment

def _check_to_me(bot: "Bot", evnet: MessageEvent): ...
def _check_nickname(bot: "Bot", event: MessageEvent): ...
async def send(
    bot: "Bot",
    event: Event,
    message: Union[str, Message, MessageSegment],
    at_sender: bool = ...,
    reply_message: bool = ...,
    **kwargs: Any,
) -> Any: ...

class Bot(BaseBot):
    async def handle_event(self, event: Event) -> None: ...
    async def send(
        self, event: Event, message: Union[str, Message, MessageSegment], **kwargs: Any
    ) -> Any: ...
    async def get_latest_events(self, *, limit: int, timeout: int) -> List[Event]:
        """获取最新事件列表

        参数：
            limit： 获取的事件数量上限，0 表示不限制
            timeout：没有事件时要等待的秒数，0 表示使用短轮询，不等待
        """
        ...
    async def get_supported_actions(self) -> List[str]:
        """获取支持的动作列表"""
        ...
    async def get_status(self) -> Dict[str, bool]:
        """获取运行状态"""
        ...
    async def get_version(self) -> Dict[str, str]:
        """获取版本信息"""
        ...
    async def send_message(
        self,
        *,
        detail_type: str,
        user_id: Optional[str] = ...,
        group_id: Optional[str] = ...,
        guild_id: Optional[str] = ...,
        channel_id: Optional[str] = ...,
        message: Union[str, Message],
    ) -> Dict[str, Any]:
        """发送消息

        参数：
            detail_type：发送的类型，可以为 private、group 或扩展的类型，和消息事件的 detail_type 字段对应
            group_id：群 ID，当 detail_type 为 group 时必须传入
            user_id：用户 ID，当 detail_type 为 private 时必须传入
            message：消息内容，可以是字符串或 Message 对象
        """
        ...
    async def delete_message(self, *, message_id: str):
        """撤回消息

        参数：
            message_id：唯一的消息 ID
        """
        ...
    async def get_self_info(self) -> Dict[str, str]:
        """获取机器人自身信息"""
        ...
    async def get_user_info(self, *, user_id: str) -> Dict[str, str]:
        """获取用户信息

        参数：
            user_id：用户 ID，可以是好友，也可以是陌生人
        """
        ...
    async def get_friend_list(self) -> List[Dict[str, str]]:
        """获取好友列表"""
        ...
    async def get_group_info(self, *, group_id: str) -> Dict[str, str]:
        """获取群信息

        参数：
            group_id：群 ID
        """
        ...
    async def get_group_list(self) -> List[Dict[str, str]]:
        """获取群列表"""
        ...
    async def get_group_member_info(
        self, *, group_id: str, user_id: str
    ) -> Dict[str, str]:
        """获取群成员信息

        参数：
            group_id：群 ID
            user_id：用户 ID
        """
        ...
    async def get_group_member_list(self, *, group_id: str) -> List[Dict[str, str]]:
        """获取群成员列表

        参数：
            group_id：群 ID
        """
        ...
    async def set_group_name(self, *, group_id: str, group_name: str) -> None:
        """设置群名称

        参数：
            group_id：群 ID
            group_name：群名称
        """
        ...
    async def leave_group(self, *, group_id: str) -> None:
        """退出群

        参数：
            group_id：群 ID
        """
        ...
    async def kick_group_member(self, *, group_id: str, user_id: str) -> None:
        """踢出群成员

        参数：
            group_id：群 ID
            user_id：用户 ID
        """
        ...
    async def ban_group_member(self, *, group_id: str, user_id: str) -> None:
        """禁言群成员

        参数：
            group_id：群 ID
            user_id：用户 ID
        """
        ...
    async def unban_group_member(self, *, group_id: str, user_id: str) -> None:
        """解除禁言群成员

        参数：
            group_id：群 ID
            user_id：用户 ID
        """
        ...
    async def set_group_admin(self, *, group_id: str, user_id: str) -> None:
        """设置管理员

        参数：
            group_id：群 ID
            user_id：用户 ID
        """
        ...
    async def unset_group_admin(self, *, group_id: str, user_id: str) -> None:
        """解除管理员

        参数：
            group_id：群 ID
            user_id：用户 ID
        """
        ...
